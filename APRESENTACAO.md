# Checklist de apresentação + evidências (Tech Challenge)

## Materiais prontos para gravação

- Roteiro detalhado do vídeo (10 min): [docs/ROTEIRO_VIDEO.md](docs/ROTEIRO_VIDEO.md)
- Script com queries do Athena: [docs/athena_queries.sql](docs/athena_queries.sql)

## Estado “limpo” esperado (antes do vídeo)

### S3 (bucket `pos-tech-b3-pipeline-cezar-2026`)
- Deve existir: `raw/`, `refined/`, `athena-results/`, `glue-scripts/`, `lambda-deployments/`.
- Em `refined/`, deve existir **apenas**: `dataset=petr4/` (ou outros `dataset=.../` se vocês usarem mais).
- Não deve existir (para evitar confusão): `refined/daily/`, `refined/monthly/`, `refined/summary/`.
- Apagar objetos 0B do tipo `*_\$folder\$` (só limpeza visual do console).

### Glue Catalog (database `b3-pipeline-db-dev`)
- Deve existir **1 tabela principal**: `dataset_petr4`.

### Glue Crawler
- Manter: `b3-pipeline-crawler-refined-dev`.
- Data source ideal do crawler: `s3://pos-tech-b3-pipeline-cezar-2026/refined/` **desde que** `refined/` não tenha `daily/monthly/summary`.

### Athena
- Use o workgroup do projeto (se existir): `b3-pipeline-athena-dev`.
- Database: `b3-pipeline-db-dev`.

---

## Evidências (prints) mínimas para cobrir R1–R8

1) **R1 (scraping diário)**
- Print do CloudWatch Logs da Lambda `b3-pipeline-scraping-dev` mostrando execução e datas (granularidade diária).

2) **R2 (RAW parquet particionado por data)**
- Print do S3 em `raw/dataset=petr4/ticker=petr4/year=YYYY/month=MM/day=DD/` com arquivo `.parquet`.

3) **R3/R4 (S3 aciona Lambda, que chama Glue)**
- Print da configuração do evento (S3 notification) no bucket.
- Print do CloudWatch Logs da Lambda `b3-pipeline-trigger-glue-dev` mostrando `StartJobRun` do Glue.

4) **R5 (transformações no Glue Job)**
- Print do job run `b3-pipeline-etl-dev` como `SUCCEEDED`.
- Print do log do Glue mostrando as etapas e o resumo (renomeações e cálculos).

5) **R6 (REFINED parquet particionado por data e ticker)**
- Print do S3 em `refined/dataset=petr4/ticker=petr4/year=YYYY/month=MM/day=DD/`.

6) **R7 (Catalogação automática)**
- Print do crawler `b3-pipeline-crawler-refined-dev` com `Last run status: Succeeded`.
- Print do Glue Catalog `b3-pipeline-db-dev` mostrando a tabela `dataset_petr4`.

7) **R8 (Athena SQL)**
- Print do Athena rodando uma query (aba com “Completed”) + resultado.

---

## Sequência de queries para a demo (Athena)

> No Athena: selecione `AwsDataCatalog` e database `b3-pipeline-db-dev`.

### Q1 — listar tabelas (sanidade)
```sql
SHOW TABLES;
```

### Q2 — mostrar dados + colunas renomeadas (R5-B)
```sql
SELECT
  date,
  open,
  high,
  low,
  preco_fechamento,
  volume_negociado
FROM dataset_petr4
ORDER BY date DESC
LIMIT 10;
```

### Q3 — mostrar cálculos temporais (R5-C)
```sql
SELECT
  date,
  preco_fechamento,
  preco_dia_anterior,
  variacao_percentual_diaria,
  preco_media_movel_5d,
  volume_media_movel_5d
FROM dataset_petr4
ORDER BY date DESC
LIMIT 15;
```

### Q4 — provar partições (R6) e “dado por dia”
```sql
SELECT
  ticker,
  year,
  month,
  day,
  COUNT(*) AS linhas
FROM dataset_petr4
GROUP BY 1,2,3,4
ORDER BY year DESC, month DESC, day DESC
LIMIT 20;
```

### Q5 — agregação mensal (R5-A) demonstrada via SQL
```sql
SELECT
  ticker,
  year,
  month,
  COUNT(*) AS qtd_dias,
  AVG(preco_fechamento) AS preco_medio,
  SUM(volume_negociado) AS volume_total
FROM dataset_petr4
GROUP BY 1,2,3
ORDER BY year DESC, month DESC;
```

### Q6 — resumo do período (R5-A)
```sql
SELECT
  ticker,
  MIN(date) AS data_inicio,
  MAX(date) AS data_fim,
  COUNT(*) AS total_dias,
  AVG(preco_fechamento) AS preco_medio_periodo,
  SUM(volume_negociado) AS volume_total_periodo
FROM dataset_petr4
GROUP BY 1;
```
