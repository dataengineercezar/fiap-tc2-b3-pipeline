# Tech Challenge (FIAP) — Pipeline Batch B3 (PETR4)

Este documento é um resumo executivo do projeto e um guia rápido para avaliação/execução, para ser anexado na entrega.

## Repositório

- Repo (HTTPS): https://github.com/dataengineercezar/fiap-tc2-b3-pipeline.git
- Branch: main
- Commit (HEAD): 8402db509951ede854b0abe485ee0723267cd3e1

## Objetivo

Construir um pipeline batch completo na AWS para extrair, processar e consultar dados diários de ações/índices da B3 (ex.: PETR4), usando S3 + Lambda + Glue + Glue Catalog + Athena.

## Arquitetura (alto nível)

Fluxo ponta-a-ponta:

1) (Opcional) EventBridge agenda a execução diária
2) Lambda Scraping extrai dados (granularidade diária) e grava no S3 (camada RAW) em Parquet particionado por data
3) Evento do S3 (ObjectCreated em `raw/`) aciona a Lambda Trigger
4) Lambda Trigger inicia o Glue Job (ETL)
5) Glue Job processa/transforma e grava no S3 (camada REFINED) em Parquet particionado por data e ticker
6) Glue Crawler atualiza o Glue Data Catalog (tabela)
7) Athena consulta os dados via SQL

Componentes AWS (ambiente dev usado no vídeo):

- Região: sa-east-1
- S3 bucket: pos-tech-b3-pipeline-cezar-2026
- Lambdas:
  - Scraping: b3-pipeline-scraping-dev
  - Trigger Glue: b3-pipeline-trigger-glue-dev
- Glue:
  - Job ETL: b3-pipeline-etl-dev
  - Crawler: b3-pipeline-crawler-refined-dev
  - Data Catalog database: b3-pipeline-db-dev
  - Tabela principal: dataset_petr4
- Athena workgroup: b3-pipeline-athena-dev
- EventBridge rule (schedule): b3-pipeline-scraping-schedule-dev

## Requisitos (R1–R8) — como foi atendido

- R1: Lambda faz scraping/extração diária (fonte: BRAPI)
- R2: Dados brutos no S3 em Parquet com partição diária
- R3: Bucket S3 aciona uma Lambda ao receber objeto em `raw/`
- R4: Lambda trigger apenas inicia o Glue Job (StartJobRun)
- R5: Glue Job realiza transformações obrigatórias:
  - (A) agregação/sumarização (demonstrada via SQL no Athena)
  - (B) renomeio de 2 colunas (ex.: `preco_fechamento`, `volume_negociado`)
  - (C) cálculo temporal (ex.: média móvel / variação diária / preço dia anterior)
- R6: Dados refinados salvos em `refined/` (Parquet) e particionados por data e ticker
- R7: Crawler cataloga automaticamente no Glue Catalog (tabela no database)
- R8: Consultas SQL via Athena

Requisitos oficiais do enunciado: ver [requisitos.txt](requisitos.txt)

## Estrutura do Data Lake (S3)

Layout esperado (padrão para demo):

- RAW (bronze):
  - `raw/dataset=petr4/ticker=petr4/year=YYYY/month=MM/day=DD/data.parquet`
- REFINED (silver):
  - `refined/dataset=petr4/ticker=petr4/year=YYYY/month=MM/day=DD/part-*.parquet`

## Artefatos do repositório

- Documentação geral do projeto: [README.md](README.md)
- Requisitos oficiais do enunciado: [requisitos.txt](requisitos.txt)
- Queries SQL para validação no Athena (R5/R8): [docs/athena_queries.sql](docs/athena_queries.sql)
- Infra como código (Terraform): [terraform](terraform)
- Scripts de build/deploy: [scripts](scripts)

## Código-fonte (principais arquivos)

- Lambda scraping (R1/R2): [src/lambda/lambda_scraping.py](src/lambda/lambda_scraping.py)
- Lambda trigger Glue (R3/R4): [src/lambda/lambda_trigger_glue.py](src/lambda/lambda_trigger_glue.py)
- Glue ETL (R5/R6/R7): [src/glue/glue_etl_job.py](src/glue/glue_etl_job.py)

## Infraestrutura (Terraform)

- Infra do projeto: [terraform](terraform)
- Scripts de apoio (build/deploy): [scripts](scripts)
- Guia de validações no Console: [docs/VALIDACAO_ETAPA3_CONSOLE_AWS.md](docs/VALIDACAO_ETAPA3_CONSOLE_AWS.md)

Observações:

- No Windows, os scripts `.sh` são executados via WSL.
- Não versionar `terraform.tfstate*` nem `tfplan`.

### Deploy (fluxo típico)

Pré-requisitos:

- AWS CLI autenticado (via `aws configure` / profile)
- Terraform instalado
- WSL (para rodar scripts `.sh` no Windows)

Passos:

1) Empacotar Lambdas (gera ZIPs em `build/`):

```bash
bash scripts/build_lambda_scraping.sh
bash scripts/build_lambda_trigger_glue.sh
```

2) Aplicar Terraform (ambiente dev):

```bash
bash scripts/terraform_apply_etapa3.sh
```

Validação pós-deploy (Console AWS): ver [docs/VALIDACAO_ETAPA3_CONSOLE_AWS.md](docs/VALIDACAO_ETAPA3_CONSOLE_AWS.md)

## Observações de avaliação

- O projeto atende aos requisitos R1–R8 conforme mapeamento acima.
- As validações técnicas podem ser feitas consultando os artefatos do repositório e executando as queries em [docs/athena_queries.sql](docs/athena_queries.sql).
