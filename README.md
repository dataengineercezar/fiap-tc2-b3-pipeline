# Tech Challenge (FIAP) — Pipeline Batch B3 (PETR4)

Pipeline batch completo na AWS para extrair, processar e consultar dados de ações da B3 (ex.: PETR4), usando **S3 + Lambda + Glue + Glue Catalog + Athena**.

**Links rápidos**
- Apresentação (checklist + evidências): [APRESENTACAO.md](APRESENTACAO.md)
- Roteiro do vídeo (até 10 min): [docs/ROTEIRO_VIDEO.md](docs/ROTEIRO_VIDEO.md)
- Queries do Athena (copiar/colar): [docs/athena_queries.sql](docs/athena_queries.sql)
- Infra (Terraform): [terraform](terraform)

## Sumário

- [O que este projeto entrega (R1–R8)](#o-que-este-projeto-entrega-r1r8)
- [Arquitetura (alto nível)](#arquitetura-alto-n%C3%ADvel)
- [Estrutura do Data Lake (S3)](#estrutura-do-data-lake-s3)
- [Resultados esperados (prints rápidos)](#resultados-esperados-prints-r%C3%A1pidos)
- [Para apresentação (vídeo / evidências)](#para-apresenta%C3%A7%C3%A3o-v%C3%ADdeo--evid%C3%AAncias)
- [Componentes (código)](#componentes-c%C3%B3digo)
- [Infra (Terraform)](#infra-terraform)
- [Demo rápida (5–8 min)](#demo-r%C3%A1pida-5%E2%80%938-min)
- [Setup local (opcional)](#setup-local-opcional)
- [Segurança / higiene do repositório](#seguran%C3%A7a--higiene-do-reposit%C3%B3rio)

---

## O que este projeto entrega (R1–R8)

| Requisito | Como é atendido |
|---|---|
| R1 | Lambda faz scraping/extração diária (BRAPI) |
| R2 | Dados brutos no S3 em **Parquet** com partição diária |
| R3 | Chegada no S3 `raw/` aciona Lambda trigger |
| R4 | Lambda trigger **apenas inicia** o Glue Job |
| R5-A | Agregação/sumarização (demonstrada via SQL no Athena) |
| R5-B | Renomeio de 2 colunas no ETL (ex.: `preco_fechamento`, `volume_negociado`) |
| R5-C | Cálculo temporal (ex.: média móvel, variação diária) |
| R6 | Dados refinados em Parquet em `refined/`, particionado por data e ticker |
| R7 | Crawler cataloga automaticamente no Glue Catalog |
| R8 | Consultas SQL via Athena |

## Arquitetura (alto nível)

Diagrama do fluxo ponta-a-ponta (o que você deve mostrar no vídeo):

```mermaid
flowchart LR
	EB[EventBridge<br/>(opcional)] --> LS[Lambda Scraping<br/>R1]
	LS --> RAW[(S3 RAW<br/>Parquet + partição diária<br/>R2)]
	RAW -->|ObjectCreated em raw/| LT[Lambda Trigger Glue<br/>R3/R4]
	LT --> GJ[Glue Job ETL<br/>R5/R6]
	GJ --> REF[(S3 REFINED<br/>Parquet + partição por data+ticker<br/>R6)]
	GJ --> CR[Glue Crawler<br/>R7]
	CR --> GC[(Glue Data Catalog<br/>Tabela)]
	GC --> ATH[Athena SQL<br/>R8]
```

Componentes AWS envolvidos:
- **S3** (raw/refined)
- **Lambda** (scraping + trigger)
- **Glue** (job ETL + crawler + catalog)
- **Athena** (consultas SQL)
- **EventBridge** (agendamento diário, opcional)

## Estrutura do Data Lake (S3)

Layout esperado (padrão “limpo” para demo):

```text
s3://<bucket>/
	raw/
		dataset=petr4/
			ticker=petr4/
				year=YYYY/
					month=MM/
						day=DD/
							data.parquet
	refined/
		dataset=petr4/
			ticker=petr4/
				year=YYYY/
					month=MM/
						day=DD/
							part-*.parquet
```

- RAW (bronze): `s3://<bucket>/raw/dataset=petr4/ticker=petr4/year=YYYY/month=MM/day=DD/data.parquet`
- REFINED (silver): `s3://<bucket>/refined/dataset=petr4/ticker=petr4/year=YYYY/month=MM/day=DD/` (Parquet)

> Nota: para manter o ambiente “limpo” para apresentação, agregações (mensal/summary) são demonstradas **via SQL** no Athena (sem criar árvores extras no S3).

## Resultados esperados (prints rápidos)

Se alguém abrir este repositório e quiser validar “em 30 segundos”, estes são os prints que comprovam tudo:

1) **S3 RAW (R2)**
- Print do Console em `raw/dataset=petr4/ticker=petr4/year=YYYY/month=MM/day=DD/` mostrando `data.parquet`.

2) **S3 REFINED (R6)**
- Print do Console em `refined/dataset=petr4/ticker=petr4/year=YYYY/month=MM/day=DD/` mostrando `part-*.parquet`.

3) **Glue Job run (R5)**
- Print do Glue Job com um run `SUCCEEDED`.

4) **Glue Catalog (R7)**
- Print do Database/Tabela no Data Catalog (ex.: tabela `dataset_petr4`).

5) **Athena (R8)**
- Print do Athena com status `Completed` e resultado de uma query simples (ex.: `SELECT * ... LIMIT 10`).

## Para apresentação (vídeo / evidências)

Tudo que você precisa para gravar está aqui:
- [APRESENTACAO.md](APRESENTACAO.md)
- [docs/ROTEIRO_VIDEO.md](docs/ROTEIRO_VIDEO.md)
- [docs/athena_queries.sql](docs/athena_queries.sql)

## Componentes (código)

- Lambda scraping (R1/R2): [src/lambda/lambda_scraping.py](src/lambda/lambda_scraping.py)
- Lambda trigger Glue (R3/R4): [src/lambda/lambda_trigger_glue.py](src/lambda/lambda_trigger_glue.py)
- Glue ETL (R5/R6/R7): [src/glue/glue_etl_job.py](src/glue/glue_etl_job.py)

## Infra (Terraform)

- IaC do projeto: [terraform](terraform)
- Scripts de apoio: [scripts](scripts)
- Validações no Console (guia): [docs/VALIDACAO_ETAPA3_CONSOLE_AWS.md](docs/VALIDACAO_ETAPA3_CONSOLE_AWS.md)

### Pré-requisitos

- AWS CLI autenticado (`aws configure` / profile)
- Terraform (versão compatível com o projeto)
- Bash (no Windows, usar WSL para executar scripts `.sh`)

### Deploy (fluxo típico)

1) Empacotar Lambdas (gera ZIPs em `build/`):

```bash
bash scripts/build_lambda_scraping.sh
bash scripts/build_lambda_trigger_glue.sh
```

2) Aplicar Terraform (ambiente dev):

```bash
bash scripts/terraform_apply_etapa3.sh
```

## Demo rápida (5–8 min)

1) Execute a Lambda de scraping (manual ou via EventBridge) e confirme um novo Parquet em `raw/`.
2) Confirme no CloudWatch Logs que a Lambda trigger chamou o Glue (StartJobRun).
3) No Glue, valide um Job Run `SUCCEEDED`.
4) No S3, valide o output em `refined/` no padrão `dataset=.../ticker=.../year/month/day/`.
5) Rode o crawler (ou valide `Last run status: Succeeded`) e confirme a tabela no Glue Catalog.
6) No Athena, rode as queries em [docs/athena_queries.sql](docs/athena_queries.sql).

## Setup local (opcional)

Para testes locais (scripts auxiliares):

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Segurança / higiene do repositório

- **Nunca** versionar credenciais (`.aws/`) ou Terraform state/plan (`terraform.tfstate*`, `tfplan`).
- O projeto já possui regras no `.gitignore`, mas valide antes de dar push.
