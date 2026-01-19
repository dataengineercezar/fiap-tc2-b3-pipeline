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
from datetime import datetime
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql import functions as F
from pyspark.sql.window import Window

# Parâmetros do Job
args = getResolvedOptions(sys.argv, [
    'JOB_NAME',
    'S3_BUCKET',
    'DATASET',
    'TICKER'
])

# Inicialização
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

print("=" * 70)
print("GLUE ETL JOB - INICIANDO")
print(f"Dataset: {args['DATASET']}")
print(f"Ticker: {args['TICKER']}")
print(f"Bucket: {args['S3_BUCKET']}")
print("=" * 70)


# ===================================================================
# ETAPA 1: LEITURA DOS DADOS RAW
# ===================================================================
print("\n[1/5] Lendo dados RAW do S3...")

input_path = f"s3://{args['S3_BUCKET']}/raw/dataset={args['DATASET']}/ticker={args['TICKER']}/"
print(f"Input Path: {input_path}")

# Ler CSV (dados novos do Lambda) OU Parquet (dados históricos)
df_raw = None

# Tentativa 1: CSV
try:
    print("Tentando ler CSV...")
    df_raw = spark.read \
        .option("header", "true") \
        .option("inferSchema", "true") \
        .csv(input_path + "**/*.csv")
    
    count = df_raw.count()
    if count > 0:
        print(f"✅ Registros CSV lidos: {count}")
    else:
        print("⚠️  CSV vazio")
        df_raw = None
except Exception as e:
    print(f"⚠️  Erro ao ler CSV: {e}")
    df_raw = None

# Tentativa 2: Parquet (se CSV falhou)
if df_raw is None:
    try:
        print("Tentando ler Parquet...")
        df_raw = spark.read.parquet(input_path)
        count = df_raw.count()
        print(f"✅ Registros Parquet lidos: {count}")
    except Exception as e:
        print(f"❌ Erro ao ler Parquet: {e}")
        raise ValueError(f"Nenhum dado encontrado em {input_path}")

if df_raw is None:
    raise ValueError("DataFrame vazio após leitura")

df_raw.printSchema()


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

# Adicionar colunas de agrupamento temporal
df_with_periods = df_with_calculations \
    .withColumn("Year", F.year("Date")) \
    .withColumn("Month", F.month("Date")) \
    .withColumn("Week", F.weekofyear("Date"))

# Agregações mensais
df_monthly_agg = df_with_periods.groupBy("ticker", "dataset", "Year", "Month").agg(
    F.count("*").alias("Qtd_Dias_Negociacao"),
    F.avg("Preco_Fechamento").alias("Preco_Medio_Mensal"),
    F.min("Low").alias("Preco_Minimo_Mensal"),
    F.max("High").alias("Preco_Maximo_Mensal"),
    F.sum("Volume_Negociado").alias("Volume_Total_Mensal"),
    F.avg("Volume_Negociado").alias("Volume_Medio_Mensal"),
    F.stddev("Preco_Fechamento").alias("Preco_Desvio_Padrao"),
    F.first("Date").alias("Primeira_Data"),
    F.last("Date").alias("Ultima_Data")
).withColumn("Periodo", F.concat(F.col("Year"), F.lit("-"), F.lpad(F.col("Month"), 2, "0")))

print(f"✅ Agregações mensais criadas: {df_monthly_agg.count()} registros")
print("   - Qtd_Dias_Negociacao (COUNT)")
print("   - Preco_Medio_Mensal (AVG)")
print("   - Volume_Total_Mensal (SUM)")
print("   - Volume_Medio_Mensal (AVG)")
print("   - Preco_Desvio_Padrao (STDDEV)")

# Agregação geral (totalizador)
df_total_agg = df_with_periods.groupBy("ticker", "dataset").agg(
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
# ETAPA 5: ESCRITA DOS DADOS REFINADOS NO S3
# ===================================================================
print("\n[5/5] Escrevendo dados refinados no S3...")

# Output 1: Dados diários com transformações
output_daily_path = f"s3://{args['S3_BUCKET']}/refined/dataset={args['DATASET']}/ticker={args['TICKER']}/daily/"
print(f"Output Daily Path: {output_daily_path}")

df_with_calculations \
    .repartition(1) \
    .write \
    .mode("overwrite") \
    .partitionBy("year", "month", "day") \
    .parquet(output_daily_path)

print(f"✅ Dados diários escritos: {df_with_calculations.count()} registros")

# Output 2: Agregações mensais
output_monthly_path = f"s3://{args['S3_BUCKET']}/refined/dataset={args['DATASET']}/ticker={args['TICKER']}/monthly/"
print(f"Output Monthly Path: {output_monthly_path}")

df_monthly_agg \
    .repartition(1) \
    .write \
    .mode("overwrite") \
    .parquet(output_monthly_path)

print(f"✅ Agregações mensais escritas: {df_monthly_agg.count()} registros")

# Output 3: Agregação total
output_total_path = f"s3://{args['S3_BUCKET']}/refined/dataset={args['DATASET']}/ticker={args['TICKER']}/summary/"
print(f"Output Total Path: {output_total_path}")

df_total_agg \
    .repartition(1) \
    .write \
    .mode("overwrite") \
    .parquet(output_total_path)

print(f"✅ Agregação total escrita: {df_total_agg.count()} registro")


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
print(f"  2. Monthly: {output_monthly_path}")
print(f"  3. Summary: {output_total_path}")
print("=" * 70)

job.commit()
