"""
Script para converter Parquet (timestamp nanos) → Parquet (timestamp micros)
Mantém formato Parquet conforme R2 do Tech Challenge
Corrige incompatibilidade Spark com timestamp nanosegundos
"""

import boto3
import pandas as pd
from io import BytesIO
import pyarrow as pa
import pyarrow.parquet as pq

s3 = boto3.client('s3')
bucket = 'pos-tech-b3-pipeline-cezar-2026'

# Listar arquivos Parquet
print("Listando arquivos Parquet...")
response = s3.list_objects_v2(
    Bucket=bucket,
    Prefix='raw/dataset=petr4/ticker=petr4/'
)

parquet_files = [obj['Key'] for obj in response.get('Contents', []) 
                 if obj['Key'].endswith('.parquet')]

print(f"Encontrados {len(parquet_files)} arquivos Parquet")
print("🧪 TESTANDO com 3 arquivos primeiro...\n")

converted = 0
errors = 0

# Testar com 3 arquivos primeiro
for s3_key in parquet_files[:3]:
    try:
        # Download Parquet original
        obj = s3.get_object(Bucket=bucket, Key=s3_key)
        parquet_data = obj['Body'].read()
        
        # Ler com pandas (tolera timestamp nanos)
        df = pd.read_parquet(BytesIO(parquet_data))
        
        # Converter Date para string ANTES de aplicar schema
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d')
        
        # Garantir tipos corretos
        df['Open'] = df['Open'].astype(float)
        df['High'] = df['High'].astype(float)
        df['Low'] = df['Low'].astype(float)
        df['Close'] = df['Close'].astype(float)
        df['Volume'] = df['Volume'].astype('int64')
        df['ticker'] = df['ticker'].astype(str)
        
        # Definir schema PyArrow (Date como string, compatível com Spark)
        schema = pa.schema([
            ('Date', pa.string()),
            ('Open', pa.float64()),
            ('High', pa.float64()),
            ('Low', pa.float64()),
            ('Close', pa.float64()),
            ('Volume', pa.int64()),
            ('ticker', pa.string())
        ])
        
        # Criar PyArrow Table
        table = pa.Table.from_pandas(df, schema=schema, preserve_index=False)
        
        # Escrever Parquet sem timestamp problemático
        buffer = BytesIO()
        pq.write_table(
            table, 
            buffer,
            version='2.6'  # Parquet 2.6 compatível com Spark
        )
        buffer.seek(0)
        
        # Upload Parquet corrigido (sobrescrever)
        s3.put_object(
            Bucket=bucket,
            Key=s3_key,
            Body=buffer.getvalue(),
            ContentType='application/x-parquet'
        )
        
        converted += 1
        print(f"✅ {converted}/3: {s3_key}")
        
    except Exception as e:
        errors += 1
        print(f"❌ Erro em {s3_key}: {e}")

print(f"\n✅ CONCLUÍDO: {converted} arquivos Parquet reescritos")
print(f"❌ Erros: {errors}")
