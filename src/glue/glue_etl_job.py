"""
Glue ETL Job - Transformações de dados B3
Atende Requisitos R5 (A, B, C) do Tech Challenge

Transformações implementadas:
A) Agrupamento numérico: GROUP BY por ticker com agregações (AVG, SUM, COUNT)
B) Renomear colunas: Close -> Preco_Fechamento, Volume -> Volume_Negociado
C) Cálculo com base na data: Moving Average 5 dias, Variação Percentual

Input: s3://bucket/raw/dataset=petr4/ticker=petr4/year=YYYY/month=MM/day=DD/
Output: s3://bucket/refined/dataset=petr4/ticker=petr4/year=YYYY/month=MM/day=DD/
"""

import sys

import boto3
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql import functions as F
from pyspark.sql.window import Window


def list_parquet_files(bucket: str, prefix: str) -> list[str]:
    s3 = boto3.client("s3", region_name="sa-east-1")
    paginator = s3.get_paginator("list_objects_v2")
    uris: list[str] = []
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            key = obj.get("Key")
            if key and key.endswith(".parquet"):
                uris.append(f"s3://{bucket}/{key}")
    return sorted(uris)

# Parâmetros do Job
args = getResolvedOptions(sys.argv, [
    'JOB_NAME',
    'S3_BUCKET',
    'DATASET',
    'TICKER',
    'CRAWLER_NAME'
])

# Inicialização
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session

# Desabilitar leitura vetorizada do Parquet para permitir conversão de tipos
spark.conf.set("spark.sql.parquet.enableVectorizedReader", "false")
spark.conf.set("spark.sql.sources.partitionOverwriteMode", "dynamic")

job = Job(glueContext)
job.init(args['JOB_NAME'], args)

print("=" * 70)
print("GLUE ETL JOB - INICIANDO")
print(f"Dataset: {args['DATASET']}")
print(f"Ticker: {args['TICKER']}")
print(f"Bucket: {args['S3_BUCKET']}")
print(f"Crawler: {args['CRAWLER_NAME']}")
print("=" * 70)


# ===================================================================
# ETAPA 1: LEITURA DOS DADOS RAW
# ===================================================================
print("\n[1/5] Lendo dados RAW do S3...")

input_path = f"s3://{args['S3_BUCKET']}/raw/dataset={args['DATASET']}/ticker={args['TICKER']}/"
print(f"Input Path: {input_path}")

# Ler Parquet (formato mandatório por R2 do Tech Challenge)
try:
    print("Listando arquivos Parquet (S3) e lendo arquivo-a-arquivo para evitar conflito de schema...")

    input_prefix = f"raw/dataset={args['DATASET']}/ticker={args['TICKER']}/"
    parquet_files = list_parquet_files(args["S3_BUCKET"], input_prefix)

    if not parquet_files:
        raise ValueError(f"Nenhum arquivo Parquet encontrado em {input_path}")

    print(f"✅ Arquivos Parquet encontrados: {len(parquet_files)}")

    dfs = []
    for uri in parquet_files:
        df_part = spark.read.parquet(uri)

        # Normalizar nomes: usar 'ticker' como chave (coluna pode vir como 'Ticker' no arquivo)
        if "ticker" not in df_part.columns and "Ticker" in df_part.columns:
            df_part = df_part.withColumnRenamed("Ticker", "ticker")

        # Forçar tipos numéricos para double (elimina long vs double)
        for col_name in ["Open", "High", "Low", "Close", "Volume"]:
            if col_name in df_part.columns:
                df_part = df_part.withColumn(col_name, F.col(col_name).cast("double"))

        # Padronizar Date como string
        if "Date" in df_part.columns:
            df_part = df_part.withColumn("Date", F.col("Date").cast("string"))

        # Remover partições físicas do raw (recriadas depois)
        columns_to_drop = [c for c in ["year", "month", "day"] if c in df_part.columns]
        if columns_to_drop:
            df_part = df_part.drop(*columns_to_drop)

        dfs.append(df_part)

    df_raw = dfs[0]
    for df_part in dfs[1:]:
        df_raw = df_raw.unionByName(df_part, allowMissingColumns=True)
    
    count = df_raw.count()
    print(f"✅ Registros lidos: {count}")
    
    if count == 0:
        raise ValueError(f"Nenhum registro encontrado em {input_path}")
    
    df_raw.printSchema()
    print(f"Colunas do DataFrame: {df_raw.columns}")
    
except Exception as e:
    print(f"❌ Erro ao ler Parquet: {e}")
    raise ValueError(f"Falha ao ler dados Parquet de {input_path}: {e}")



# ===================================================================
# ETAPA 2: TRANSFORMAÇÃO B - RENOMEAR COLUNAS (Requisito R5-B)
# ===================================================================
print("\n[2/5] TRANSFORMAÇÃO B: Renomeando colunas...")

df_renamed = df_raw \
    .withColumnRenamed("Close", "Preco_Fechamento") \
    .withColumnRenamed("Volume", "Volume_Negociado")

print("✅ Colunas renomeadas:")
print("   - Close → Preco_Fechamento")
print("   - Volume → Volume_Negociado")


# ===================================================================
# ETAPA 3: TRANSFORMAÇÃO C - CÁLCULOS COM BASE NA DATA (Requisito R5-C)
# ===================================================================
print("\n[3/5] TRANSFORMAÇÃO C: Cálculos baseados em data...")

# Window spec para cálculos temporais
window_5d = Window \
    .partitionBy("ticker") \
    .orderBy("Date") \
    .rowsBetween(-4, 0)  # Últimos 5 dias incluindo atual

window_1d = Window \
    .partitionBy("ticker") \
    .orderBy("Date") \
    .rowsBetween(-1, 0)  # Dia anterior e atual

df_with_calculations = df_renamed \
    .withColumn(
        "Preco_Media_Movel_5d",
        F.avg("Preco_Fechamento").over(window_5d)
    ) \
    .withColumn(
        "Volume_Media_Movel_5d",
        F.avg("Volume_Negociado").over(window_5d)
    ) \
    .withColumn(
        "Preco_Dia_Anterior",
        F.lag("Preco_Fechamento", 1).over(window_1d.rowsBetween(-1, -1))
    ) \
    .withColumn(
        "Variacao_Percentual_Diaria",
        F.when(
            F.col("Preco_Dia_Anterior").isNotNull(),
            ((F.col("Preco_Fechamento") - F.col("Preco_Dia_Anterior")) / F.col("Preco_Dia_Anterior") * 100)
        ).otherwise(None)
    ) \
    .withColumn(
        "Dias_Desde_Inicio",
        F.datediff(F.col("Date"), F.lit("2025-10-20"))
    )

print("✅ Cálculos adicionados:")
print("   - Preco_Media_Movel_5d (média móvel 5 dias)")
print("   - Volume_Media_Movel_5d (média móvel 5 dias)")
print("   - Variacao_Percentual_Diaria (% mudança vs dia anterior)")
print("   - Dias_Desde_Inicio (dias desde primeira data)")


# ===================================================================
# ETAPA 4: TRANSFORMAÇÃO A - AGRUPAMENTO E AGREGAÇÕES (Requisito R5-A)
# ===================================================================
print("\n[4/5] TRANSFORMAÇÃO A: Agregações por ticker e período...")

# Criar colunas year/month/day a partir do campo Date (string "yyyy-MM-dd")
# Garantir que sejam Strings para particionamento mais seguro
df_with_periods = df_with_calculations \
    .withColumn("year", F.year(F.to_date(F.col("Date"), "yyyy-MM-dd")).cast("string")) \
    .withColumn("month", F.month(F.to_date(F.col("Date"), "yyyy-MM-dd")).cast("string")) \
    .withColumn("day", F.dayofmonth(F.to_date(F.col("Date"), "yyyy-MM-dd")).cast("string")) \
    .withColumn("Week", F.weekofyear(F.to_date(F.col("Date"), "yyyy-MM-dd")))

# Agregações mensais (R5-A: agrupamento, soma, contagem)
df_monthly_agg = df_with_periods.groupBy("ticker", "year", "month").agg(
    F.count("*").alias("Qtd_Dias_Negociacao"),
    F.avg("Preco_Fechamento").alias("Preco_Medio_Mensal"),
    F.min("Low").alias("Preco_Minimo_Mensal"),
    F.max("High").alias("Preco_Maximo_Mensal"),
    F.sum("Volume_Negociado").alias("Volume_Total_Mensal"),
    F.avg("Volume_Negociado").alias("Volume_Medio_Mensal"),
    F.stddev("Preco_Fechamento").alias("Preco_Desvio_Padrao"),
    F.first("Date").alias("Primeira_Data"),
    F.last("Date").alias("Ultima_Data")
).withColumn("Periodo", F.concat(F.col("year"), F.lit("-"), F.lpad(F.col("month"), 2, "0")))

print(f"✅ Agregações mensais criadas: {df_monthly_agg.count()} registros")
print("   - Qtd_Dias_Negociacao (COUNT)")
print("   - Preco_Medio_Mensal (AVG)")
print("   - Volume_Total_Mensal (SUM)")
print("   - Volume_Medio_Mensal (AVG)")
print("   - Preco_Desvio_Padrao (STDDEV)")

# Agregação geral (totalizador)
df_total_agg = df_with_periods.groupBy("ticker").agg(
    F.count("*").alias("Total_Dias_Analisados"),
    F.sum("Volume_Negociado").alias("Volume_Total_Periodo"),
    F.avg("Preco_Fechamento").alias("Preco_Medio_Periodo"),
    F.min("Low").alias("Preco_Minimo_Periodo"),
    F.max("High").alias("Preco_Maximo_Periodo"),
    F.min("Date").alias("Data_Inicio"),
    F.max("Date").alias("Data_Fim")
)

print(f"✅ Agregação geral criada: {df_total_agg.count()} registro")


# ===================================================================
# ETAPA 5: ESCRITA DOS DADOS REFINADOS NO S3 (Requisito R6)
# ===================================================================
print("\n[5/5] Escrevendo dados refinados no S3...")

# Output principal (R6): refined/ particionado por data e por ação/índice (ticker) e dataset
ticker_norm = args['TICKER'].lower()
dataset_norm = args['DATASET'].lower()
output_daily_path = (
    f"s3://{args['S3_BUCKET']}/refined/"
    f"dataset={dataset_norm}/ticker={ticker_norm}/"
)
print(f"Output Daily Path: {output_daily_path}")

# Evitar metadados inválidos no Athena: colunas duplicadas com partições (ex: ticker=...)
df_daily_out = df_with_periods
for col_to_drop in ["ticker", "dataset"]:
    if col_to_drop in df_daily_out.columns:
        df_daily_out = df_daily_out.drop(col_to_drop)

# df_daily_out já tem year, month, day como strings criadas na ETAPA 4
df_daily_out \
    .repartition(1) \
    .write \
    .mode("overwrite") \
    .partitionBy("year", "month", "day") \
    .parquet(output_daily_path)

print(f"✅ Dados diários escritos: {df_daily_out.count()} registros")

# Mantemos as agregações (R5-A) calculadas no job, mas não gravamos outputs adicionais
# para evitar poluir o S3 refined/ e criar múltiplas tabelas no Glue Catalog.
print(f"✅ Agregações mensais calculadas (R5-A): {df_monthly_agg.count()} registros")
print(f"✅ Agregação total calculada (R5-A): {df_total_agg.count()} registro")


# ===================================================================
# FINALIZAÇÃO
# ===================================================================
print("\n" + "=" * 70)
print("GLUE ETL JOB - CONCLUÍDO COM SUCESSO!")
print("=" * 70)
print("\nRESUMO DAS TRANSFORMAÇÕES:")
print(f"  ✅ R5-A: Agregações (COUNT, SUM, AVG, MIN, MAX, STDDEV)")
print(f"  ✅ R5-B: Renomeação de colunas (Close, Volume)")
print(f"  ✅ R5-C: Cálculos temporais (Moving Avg, Variação %, Dias)")
print("\nOUTPUTS GERADOS:")
print(f"  1. Daily: {output_daily_path}")
print("  2. Monthly/Summary: (não gravados; demonstrados via SQL no Athena)")
print("=" * 70)


# ===================================================================
# CATALOGAÇÃO (R7): disparar o crawler automaticamente após a escrita
# ===================================================================
print("\nIniciando Glue Crawler para catalogar dados refined (R7)...")
try:
    glue = boto3.client("glue")
    glue.start_crawler(Name=args["CRAWLER_NAME"])
    print(f"✅ Crawler iniciado: {args['CRAWLER_NAME']}")
except Exception as e:
    # Não falhar o job por causa do crawler; registrar e seguir.
    print(f"⚠️ Não foi possível iniciar o crawler automaticamente: {e}")

job.commit()
