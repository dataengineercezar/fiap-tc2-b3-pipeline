# Roteiro detalhado do vídeo (até 10 min) — Tech Challenge Fase 2

> Objetivo: demonstrar, de ponta a ponta, um pipeline batch na AWS (S3 + Lambda + Glue + Glue Catalog + Athena) atendendo R1–R8.
>
> Sugestão: grave a tela (OBS) + narração. Faça cortes rápidos (sem “esperar carregar”).

## Pré-requisitos (antes de gravar)

- Ambiente “limpo” conforme o checklist em [APRESENTACAO.md](../APRESENTACAO.md).
- Tenha em mãos:
  - Região: `sa-east-1`.
  - Bucket: `pos-tech-b3-pipeline-cezar-2026`.
  - Lambdas:
    - Scraping: `b3-pipeline-scraping-dev`
    - Trigger Glue: `b3-pipeline-trigger-glue-dev`
  - Glue:
    - Job ETL: `b3-pipeline-etl-dev`
    - Crawler: `b3-pipeline-crawler-refined-dev`
    - Data Catalog database: `b3-pipeline-db-dev`
    - Tabela principal: `dataset_petr4`
  - Athena Workgroup: `b3-pipeline-athena-dev`.
  - EventBridge rule (schedule): `b3-pipeline-scraping-schedule-dev`.
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
- Mostre rapidamente o diagrama/arquitetura (README ou slide). Aponte o fluxo: EventBridge → Lambda Scraping → S3 RAW → S3 Event → Lambda Trigger → Glue Job → S3 REFINED → Crawler/Catalog → Athena.

**Ênfase técnica (1 frase)**
- “A arquitetura é event-driven: a chegada do Parquet no S3 (raw) dispara a orquestração do ETL no Glue, e a camada refined vira tabela via Crawler/Catalog para consulta no Athena.”

### 0:40–2:00 — R1 e R2 (extração diária + RAW Parquet particionado)

**R1 (scraping diário)**
- Mostre a Lambda de scraping no Console.
- Clique em “Monitor” → “View logs in CloudWatch”.
- Mostre um log de execução, destacando que a granularidade é diária.

**O que explicar (curto, mostrando domínio)**
- Fonte: BRAPI (dados do mercado brasileiro). A Lambda monta a requisição, normaliza o payload e escreve no S3.
- Idempotência/organização: o path no S3 carrega `dataset`, `ticker` e a data (ano/mês/dia).

**R2 (RAW em Parquet com partição diária)**
- Vá ao S3 → `raw/`.
- Navegue até um caminho do tipo:
  - `raw/dataset=petr4/ticker=petr4/year=YYYY/month=MM/day=DD/`
- Mostre o(s) arquivo(s) `.parquet`.

**O que explicar (curto, mostrando domínio)**
- Por que Parquet: formato colunar, compressão e leitura eficiente no Athena/Glue.
- Por que partição diária: reduz custo/tempo de query (Athena varre só as partições necessárias).

**Fala sugerida**
- “Aqui comprovamos o requisito 1: a extração diária. E o requisito 2: os dados brutos entram no S3 em Parquet e ficam particionados por data.”

### 2:00–3:10 — R3 e R4 (S3 aciona Lambda que chama Glue)

**R3 (S3 event → Lambda)**
- No bucket S3, abra “Properties” → “Event notifications”.
- Mostre a notificação configurada para objetos em `raw/`.

**O que explicar (curto, mostrando domínio)**
- O evento filtra por prefixo/sufixo (ex.: só `raw/...` e `.parquet`) para evitar disparos desnecessários.
- Resultado: cada novo Parquet no RAW vira um gatilho para processamento.

**R4 (Lambda inicia Glue Job)**
- Abra a Lambda trigger (`trigger-glue`).
- Vá em “Monitor” → logs no CloudWatch.
- Mostre uma execução com chamada `StartJobRun` do Glue.

**O que explicar (curto, mostrando domínio)**
- A trigger não “transforma” dados: ela só extrai `dataset/ticker` do key do S3 e dispara o Job com os argumentos corretos.
- Vantagem: desacopla ingestão (Lambda) de processamento pesado (Glue).

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

**O que explicar (curto, mostrando domínio)**
- A: mostramos a capacidade de sumarizar o dado (por período) sem perder o histórico diário.
- B: renomear colunas padroniza o schema e deixa o dado pronto para consumo/negócio.
- C: cálculo temporal prova que tratamos “dado como série temporal” (ex.: médias móveis e variação diária).

**R6 (REFINED particionado por data e ticker)**
- No S3, abra `refined/`.
- Navegue até:
  - `refined/dataset=petr4/ticker=petr4/year=YYYY/month=MM/day=DD/`
- Mostre que o output está em Parquet e particionado por ticker e data.

**O que explicar (curto, mostrando domínio)**
- A camada refined é a “camada pronta para consulta”: schema consistente + partições bem definidas.
- A partição por `ticker` permite expandir para outras ações sem misturar datasets.

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

**O que explicar (curto, mostrando domínio)**
- O crawler lê a estrutura do S3 refined e materializa metadados (schema + partições) no Data Catalog.
- Isso transforma Parquet “no bucket” em tabela SQL (Athena) sem precisar criar DDL manualmente.

**Fala sugerida**
- “Após o Glue job, o crawler atualiza o Glue Catalog e cria/atualiza a tabela automaticamente, atendendo o requisito 7.”

### 7:00–9:30 — R8 (Athena SQL) + demonstração das transformações

- Vá ao Athena (Query editor).
- Selecione o Workgroup do projeto e o database do projeto.
- Cole e rode, nessa ordem, as queries do arquivo [docs/athena_queries.sql](athena_queries.sql).

**O que explicar (curto, mostrando domínio)**
- Comece com `SHOW TABLES`/`LIMIT 10` para sanidade.
- Em seguida, mostre as colunas renomeadas (R5-B) e os cálculos temporais (R5-C).
- Feche com uma agregação mensal/sumarização via SQL (R5-A) para provar análise sem criar outputs extras.

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
