"""
Lambda function para scraping diário de dados da B3
Acionada via EventBridge Schedule
Atende Requisito R1: extração automatizada de dados B3
"""

import json
import logging
import os
from datetime import datetime, timedelta

import boto3
import pandas as pd
import requests
from io import BytesIO
import pyarrow as pa
import pyarrow.parquet as pq

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def fetch_brapi_data(ticker: str, days: int = 1) -> pd.DataFrame:
    """
    Busca dados da BRAPI.DEV API
    """
    logger.info(f"Fetching data for {ticker} from BRAPI.DEV")
    
    # Calcular range
    if days <= 5:
        range_period = '5d'
    elif days <= 30:
        range_period = '1mo'
    elif days <= 90:
        range_period = '3mo'
    else:
        range_period = '1y'
    
    url = f"https://brapi.dev/api/quote/{ticker}"
    params = {
        'range': range_period,
        'interval': '1d',
        'fundamental': 'false'
    }
    
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    
    data = response.json()
    
    if 'results' not in data or not data['results']:
        raise ValueError("Empty response from API")
    
    stock_data = data['results'][0]
    historical = stock_data.get('historicalDataPrice', [])
    
    if not historical:
        raise ValueError("No historical data available")
    
    # Converter para DataFrame
    df = pd.DataFrame(historical)
    df = df.rename(columns={
        'date': 'Date',
        'open': 'Open',
        'high': 'High',
        'low': 'Low',
        'close': 'Close',
        'volume': 'Volume'
    })
    
    df['Date'] = pd.to_datetime(df['Date'], unit='s')
    df['Adj Close'] = df['Close']
    
    logger.info(f"Fetched {len(df)} records")
    
    return df


def process_data(df: pd.DataFrame, ticker: str, dataset: str) -> pd.DataFrame:
    """
    Adiciona metadados e colunas de particionamento
    """
    ticker_normalized = ticker.replace(".SA", "").lower()
    
    df['ticker'] = ticker_normalized
    df['dataset'] = dataset
    df['extraction_timestamp'] = datetime.now().isoformat()
    df['data_source'] = 'lambda_brapi_api'
    
    df['date'] = pd.to_datetime(df['Date']).dt.date
    df['year'] = pd.to_datetime(df['Date']).dt.year
    df['month'] = pd.to_datetime(df['Date']).dt.month
    df['day'] = pd.to_datetime(df['Date']).dt.day
    
    return df


def upload_to_s3(df: pd.DataFrame, bucket: str, prefix: str, ticker: str, dataset: str):
    """
    Upload para S3 com particionamento diário
    """
    s3_client = boto3.client('s3')
    ticker_normalized = ticker.replace(".SA", "").lower()
    
    uploaded_files = []
    
    for date, group in df.groupby(['year', 'month', 'day']):
        year, month, day = date
        
        s3_key = (
            f"{prefix}/dataset={dataset}/ticker={ticker_normalized}/"
            f"year={year}/month={month:02d}/day={day:02d}/data.parquet"
        )
        
        # Converter para Parquet em memória
        table = pa.Table.from_pandas(group)
        buffer = BytesIO()
        pq.write_table(table, buffer)
        buffer.seek(0)
        
        # Upload
        s3_client.put_object(
            Bucket=bucket,
            Key=s3_key,
            Body=buffer.getvalue()
        )
        
        uploaded_files.append(s3_key)
        logger.info(f"Uploaded: s3://{bucket}/{s3_key}")
    
    return uploaded_files


def lambda_handler(event, context):
    """
    Lambda handler - executado pelo EventBridge Schedule
    """
    logger.info("="*70)
    logger.info("LAMBDA SCRAPING B3 - INICIANDO")
    logger.info(f"Event: {json.dumps(event)}")
    logger.info("="*70)
    
    # Configurações (via environment variables ou event)
    ticker = os.environ.get('TICKER', 'PETR4')
    dataset = os.environ.get('DATASET', 'petr4')
    bucket = os.environ.get('S3_BUCKET')
    prefix = os.environ.get('S3_PREFIX', 'raw')
    days = int(os.environ.get('DAYS', '5'))  # Últimos 5 dias (para pegar novos)
    
    if not bucket:
        raise ValueError("S3_BUCKET environment variable is required")
    
    logger.info(f"Config: ticker={ticker}, dataset={dataset}, bucket={bucket}, days={days}")
    
    try:
        # Extrair dados
        df = fetch_brapi_data(ticker=ticker, days=days)
        
        if df.empty:
            logger.warning("No data fetched. Exiting.")
            return {
                'statusCode': 200,
                'body': json.dumps({'message': 'No new data available'})
            }
        
        # Processar
        df = process_data(df=df, ticker=ticker, dataset=dataset)
        
        # Filtrar apenas último dia (evitar duplicatas)
        latest_date = df['date'].max()
        df_today = df[df['date'] == latest_date]
        
        logger.info(f"Processing {len(df_today)} records for {latest_date}")
        
        # Upload para S3
        uploaded_files = upload_to_s3(
            df=df_today,
            bucket=bucket,
            prefix=prefix,
            ticker=ticker,
            dataset=dataset
        )
        
        logger.info("="*70)
        logger.info("LAMBDA SCRAPING B3 - CONCLUÍDO COM SUCESSO")
        logger.info(f"Files uploaded: {len(uploaded_files)}")
        logger.info("="*70)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Data scraped and uploaded successfully',
                'records_processed': len(df_today),
                'date': str(latest_date),
                'files_uploaded': uploaded_files
            })
        }
        
    except Exception as e:
        logger.error(f"ERROR: {str(e)}", exc_info=True)
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Error during scraping',
                'error': str(e)
            })
        }
