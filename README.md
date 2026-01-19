# Tech Challenge Fase 2 - Pipeline Batch B3 (PETR4)

## Arquitetura
Pipeline de dados batch para ingestão, transformação e análise de ações da B3 (PETR4.SA).

### Serviços AWS
- **S3**: Raw (JSON/Parquet) + Refined (Parquet particionado)
- **Lambda**: Trigger para iniciar Glue Job
- **Glue**: ETL (transformações obrigatórias)
- **Glue Catalog**: Metadados + tabela
- **Athena**: Queries SQL analíticas
- **EventBridge**: Agendamento diário (opcional)

## Requisitos Atendidos
- [R1] Extração diária PETR4 via BRAPI (API brasileira)
- [R2] Ingestão S3 RAW em Parquet com partição diária
- [R3] S3 Event → Lambda → Glue Job
- [R4] Lambda Python iniciando Glue
- [R5] Transformações Glue (agregação + rename + cálculo temporal)
- [R6] Dados refined particionados por data e ticker
- [R7] Catalogação automática no Glue Catalog
- [R8] Consultas SQL via Athena

## Estrutura do Data Lake (S3)
- `s3://<bucket>/raw/dataset=petr4/ticker=petr4/year=YYYY/month=MM/day=DD/data.parquet`
- `s3://<bucket>/refined/dataset=petr4/ticker=petr4/year=YYYY/month=MM/day=DD/` (Parquet)

> Observação: para manter o ambiente “limpo” para apresentação, as agregações (mensal/summary) são demonstradas via SQL no Athena.

## Componentes principais
- Lambda scraping (R1/R2): [src/lambda/lambda_scraping.py](src/lambda/lambda_scraping.py)
- Lambda trigger Glue (R3/R4): [src/lambda/lambda_trigger_glue.py](src/lambda/lambda_trigger_glue.py)
- Glue ETL (R5/R6): [src/glue/glue_etl_job.py](src/glue/glue_etl_job.py)
- Infra (Terraform): [terraform](terraform)
- Evidências e validações: [docs](docs)

## Deploy (Terraform)
Arquivos Terraform estão em [terraform](terraform). O fluxo típico é:

1) Empacotar Lambdas (gera ZIPs em `build/`):

```bash
bash scripts/build_lambda_scraping.sh
bash scripts/build_lambda_trigger_glue.sh
```

2) Aplicar Terraform (ambiente dev):

```bash
bash scripts/terraform_apply_etapa3.sh
```

## Execução (alto nível)
1) EventBridge chama a Lambda de scraping, que grava Parquet em `raw/`.
2) Notificação do S3 (ObjectCreated em `raw/`) aciona a Lambda trigger.
3) A Lambda trigger inicia o Glue Job.
4) O Glue grava outputs em `refined/` e o dado fica consultável via Athena.

## Setup Local
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```