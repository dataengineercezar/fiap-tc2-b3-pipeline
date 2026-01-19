# Roteiro detalhado do vídeo (até 10 min) — Tech Challenge Fase 2

> Objetivo: demonstrar, de ponta a ponta, um pipeline batch na AWS (S3 + Lambda + Glue + Glue Catalog + Athena) atendendo R1–R8.
>
> Sugestão: grave a tela (OBS) + narração. Faça cortes rápidos (sem “esperar carregar”).

## Pré-requisitos (antes de gravar)

- Ambiente “limpo” conforme o checklist em [APRESENTACAO.md](../APRESENTACAO.md).
- Tenha em mãos:
  - Nome do bucket (ex.: `pos-tech-b3-pipeline-cezar-2026`).
  - Nome das Lambdas (scraping e trigger-glue).
  - Nome do Glue Job e do Crawler.
  - Nome do database e tabela no Glue Catalog (ex.: `b3-pipeline-db-dev.dataset_petr4`).
  - Athena Workgroup do projeto.
- Deixe abertas (em abas) as páginas no Console:
  - S3 (bucket) — pastas `raw/` e `refined/`.
  - Lambda — funções scraping e trigger.
  - Glue — Job runs e Crawler.
  - Glue Data Catalog — Database e Table.
  - Athena — Query editor.

## Estrutura do vídeo (com tempo sugerido)

### 0:00–0:40 — Abertura (contexto + arquitetura)

**Fala sugerida**
- “Esse é o Tech Challenge da Fase 2: um pipeline batch para dados da B3. A ideia é: extrair diariamente dados da PETR4, gravar no S3 em Parquet, disparar um processamento no Glue, catalogar no Glue Catalog e consultar via Athena.”

**Tela**
- Mostre rapidamente o diagrama/arquitetura (pode ser o `README`/`docs/architecture-update.md` ou um slide). Aponte o fluxo: EventBridge → Lambda Scraping → S3 RAW → S3 Event → Lambda Trigger → Glue Job → S3 REFINED → Crawler/Catalog → Athena.

### 0:40–2:00 — R1 e R2 (extração diária + RAW Parquet particionado)

**R1 (scraping diário)**
- Mostre a Lambda de scraping no Console.
- Clique em “Monitor” → “View logs in CloudWatch”.
- Mostre um log de execução, destacando que a granularidade é diária.

**R2 (RAW em Parquet com partição diária)**
- Vá ao S3 → `raw/`.
- Navegue até um caminho do tipo:
  - `raw/dataset=petr4/ticker=petr4/year=YYYY/month=MM/day=DD/`
- Mostre o(s) arquivo(s) `.parquet`.

**Fala sugerida**
- “Aqui comprovamos o requisito 1: a extração diária. E o requisito 2: os dados brutos entram no S3 em Parquet e ficam particionados por data.”

### 2:00–3:10 — R3 e R4 (S3 aciona Lambda que chama Glue)

**R3 (S3 event → Lambda)**
- No bucket S3, abra “Properties” → “Event notifications”.
- Mostre a notificação configurada para objetos em `raw/`.

**R4 (Lambda inicia Glue Job)**
- Abra a Lambda trigger (`trigger-glue`).
- Vá em “Monitor” → logs no CloudWatch.
- Mostre uma execução com chamada `StartJobRun` do Glue.

**Fala sugerida**
- “Quando um Parquet chega no `raw/`, o S3 dispara a Lambda de trigger. Essa Lambda não transforma dados; ela apenas inicia o Glue Job, atendendo os requisitos 3 e 4.”

### 3:10–5:30 — R5 e R6 (Glue ETL + refinado particionado por data e ticker)

**R5 (transformações obrigatórias no Glue)**
- Vá ao Glue → Jobs → selecione o Job.
- Mostre o histórico de execuções (Job runs) com status `SUCCEEDED`.
- Abra os logs do job (CloudWatch) e destaque:
  - (A) agregação/sumarização (ex.: cálculos que suportam análises, e que serão demonstrados via SQL no Athena).
  - (B) renomeio de 2 colunas (ex.: `close` → `preco_fechamento`, `volume` → `volume_negociado`).
  - (C) cálculo temporal (ex.: média móvel / variação diária / preço dia anterior).

**R6 (REFINED particionado por data e ticker)**
- No S3, abra `refined/`.
- Navegue até:
  - `refined/dataset=petr4/ticker=petr4/year=YYYY/month=MM/day=DD/`
- Mostre que o output está em Parquet e particionado por ticker e data.

**Fala sugerida**
- “O Glue job executa as transformações obrigatórias e grava o resultado na pasta `refined/`, particionando por ticker e por data.”

### 5:30–7:00 — R7 (catalogação automática no Glue Catalog)

- Vá ao Glue → Crawlers.
- Mostre o crawler (ex.: `b3-pipeline-crawler-refined-dev`) com `Last run status: Succeeded`.
- Vá ao Glue Data Catalog:
  - Database (ex.: `b3-pipeline-db-dev`).
  - Tabela (ex.: `dataset_petr4`).
- Abra a tabela e mostre:
  - Colunas (incluindo as renomeadas).
  - Partitions (year/month/day e ticker, se exibido).

**Fala sugerida**
- “Após o Glue job, o crawler atualiza o Glue Catalog e cria/atualiza a tabela automaticamente, atendendo o requisito 7.”

### 7:00–9:30 — R8 (Athena SQL) + demonstração das transformações

- Vá ao Athena (Query editor).
- Selecione o Workgroup do projeto e o database do projeto.
- Cole e rode, nessa ordem, as queries do arquivo [docs/athena_queries.sql](athena_queries.sql).

**Fala sugerida (enquanto roda)**
- “Agora provamos o requisito 8: consultas SQL no Athena. Aqui vemos as colunas renomeadas e os cálculos temporais. E também uma agregação mensal/sumarização via SQL, que evidencia as transformações pedidas no requisito 5.”

**Dica de gravação**
- Grave a query com status “Completed” e a tabela de resultados visível (print/pausa rápida no resultado).

### 9:30–10:00 — Encerramento

- Recapitule rapidamente R1–R8 (1 frase por requisito).
- Se quiser, mostre o repositório (Terraform + código) por 10–15 segundos.

## Plano B (se algo falhar ao vivo)

- Se o Glue demorar: use um job run anterior `SUCCEEDED` para evidência e siga para S3 refined + Catalog + Athena.
- Se o Athena estiver lento: rode ao menos 1 query simples (LIMIT 10) e tenha prints prontos.
- Se o crawler ainda não tiver rodado: rode o crawler manualmente e mostre o “Last run status”.
