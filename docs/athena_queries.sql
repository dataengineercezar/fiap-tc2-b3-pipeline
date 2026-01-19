-- Tech Challenge — Athena Queries (R1–R8)
--
-- Ajuste conforme seu ambiente:
--   - Workgroup: selecione o workgroup do projeto no Console do Athena
--   - Database:  b3-pipeline-db-dev (exemplo)
--   - Tabela:    dataset_petr4 (exemplo)
--
-- Dica: rode de cima para baixo durante a gravação do vídeo.

-- Q0 — (opcional) confirmar contexto
-- SHOW DATABASES;

-- Q1 — listar tabelas (sanidade)
SHOW TABLES;

-- Q2 — contar linhas (sanidade)
SELECT COUNT(*) AS total_linhas
FROM dataset_petr4;

-- Q3 — ver amostra de dados (ordem mais recente)
SELECT *
FROM dataset_petr4
ORDER BY date DESC
LIMIT 10;

-- Q4 — evidenciar colunas renomeadas (R5-B)
-- Esperado (exemplo): preco_fechamento e volume_negociado
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

-- Q5 — evidenciar cálculo temporal (R5-C)
-- Esperado (exemplo): preco_dia_anterior, variacao_percentual_diaria, medias moveis
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

-- Q6 — provar partições (R6) e “dado por dia”
SELECT
  ticker,
  year,
  month,
  day,
  COUNT(*) AS linhas
FROM dataset_petr4
GROUP BY 1,2,3,4
ORDER BY year DESC, month DESC, day DESC
LIMIT 50;

-- Q7 — agregação mensal (R5-A) demonstrada via SQL
SELECT
  ticker,
  year,
  month,
  COUNT(*) AS qtd_dias,
  AVG(preco_fechamento) AS preco_medio,
  MIN(preco_fechamento) AS preco_min,
  MAX(preco_fechamento) AS preco_max,
  SUM(volume_negociado) AS volume_total
FROM dataset_petr4
GROUP BY 1,2,3
ORDER BY year DESC, month DESC;

-- Q8 — resumo do período (R5-A)
SELECT
  ticker,
  MIN(date) AS data_inicio,
  MAX(date) AS data_fim,
  COUNT(*) AS total_dias,
  AVG(preco_fechamento) AS preco_medio_periodo,
  SUM(volume_negociado) AS volume_total_periodo
FROM dataset_petr4
GROUP BY 1;

-- Q9 — (extra, opcional) top variações diárias (boa para demonstrar análise)
SELECT
  date,
  ticker,
  preco_fechamento,
  variacao_percentual_diaria
FROM dataset_petr4
WHERE variacao_percentual_diaria IS NOT NULL
ORDER BY ABS(variacao_percentual_diaria) DESC
LIMIT 10;
