"""
Lambda function para scraping diário de dados da B3 - LIGHTWEIGHT VERSION
Acionada via EventBridge Schedule
Atende Requisito R1: extração automatizada de dados B3

Salva CSV (não Parquet) para reduzir tamanho do deployment package
Glue converterá CSV → Parquet na camada refined/
"""

import json
import logging
import os
from datetime import datetime, timedelta
from io import StringIO

import boto3
import requests

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def fetch_brapi_data(ticker: str, days: int = 1) -> list:
    """
    Busca dados da BRAPI.DEV API
    Retorna lista de dicts
    """
    logger.info(f"Fetching data for {ticker} from BRAPI.DEV")
    
    # Calcular range
    if days <= 5:
        # Para poucos dias, usar endpoint /quote/{ticker}?range=5d
        url = f"https://brapi.dev/api/quote/{ticker}?range={days}d"
    else:
        # Para range maior, usar interval
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")
        
        url = f"https://brapi.dev/api/quote/{ticker}?range={days}d&interval=1d"
    
    headers = {"Accept": "application/json"}
    
    # Retry logic
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Estrutura: {"results": [{"symbol": "PETR4", "historicalDataPrice": [...]}]}
            if "results" in data and len(data["results"]) > 0:
                historical = data["results"][0].get("historicalDataPrice", [])
                logger.info(f"Fetched {len(historical)} records")
                return historical
            else:
                logger.warning(f"No data in response: {data}")
                return []
                
        except requests.exceptions.RequestException as e:
            logger.warning(f"Attempt {attempt + 1}/{max_retries} failed: {e}")
            if attempt == max_retries - 1:
                raise
    
    return []


def prepare_dataframe(raw_data: list, ticker: str) -> list:
    """
    Transforma dados brutos em formato padronizado
    Retorna lista de dicts com colunas: Date, Open, High, Low, Close, Volume, ticker
    """
    records = []
    
    for item in raw_data:
        try:
            # Timestamp UNIX → datetime
            timestamp = item.get("date")
            if timestamp:
                dt = datetime.fromtimestamp(timestamp)
                date_str = dt.strftime("%Y-%m-%d")
                
                record = {
                    "Date": date_str,
                    "Open": item.get("open", 0),
                    "High": item.get("high", 0),
                    "Low": item.get("low", 0),
                    "Close": item.get("close", 0),
                    "Volume": item.get("volume", 0),
                    "ticker": ticker.lower()
                }
                records.append(record)
        except Exception as e:
            logger.warning(f"Error processing record: {e}")
            continue
    
    return records


def save_to_s3_csv(records: list, bucket: str, prefix: str, dataset: str, ticker: str) -> list:
    """
    Salva registros em CSV no S3 com particionamento por data
    """
    s3_client = boto3.client('s3')
    ticker_normalized = ticker.lower()
    
    # Agrupar por data
    by_date = {}
    for record in records:
        date_str = record["Date"]
        if date_str not in by_date:
            by_date[date_str] = []
        by_date[date_str].append(record)
    
    uploaded_files = []
    
    for date_str, group in by_date.items():
        # Parse date para partições
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        year = dt.year
        month = dt.month
        day = dt.day
        
        s3_key = (
            f"{prefix}/dataset={dataset}/ticker={ticker_normalized}/"
            f"year={year}/month={month:02d}/day={day:02d}/data.csv"
        )
        
        # Criar CSV em memória
        csv_buffer = StringIO()
        
        # Header
        if group:
            headers = list(group[0].keys())
            csv_buffer.write(",".join(headers) + "\n")
            
            # Rows
            for row in group:
                values = [str(row.get(h, "")) for h in headers]
                csv_buffer.write(",".join(values) + "\n")
        
        # Upload
        s3_client.put_object(
            Bucket=bucket,
            Key=s3_key,
            Body=csv_buffer.getvalue(),
            ContentType='text/csv'
        )
        
        uploaded_files.append(s3_key)
        logger.info(f"Uploaded: s3://{bucket}/{s3_key}")
    
    return uploaded_files


def lambda_handler(event, context):
    """
    Lambda handler - executado pelo EventBridge Schedule
    """
    logger.info("="*70)
    logger.info("LAMBDA SCRAPING B3 - INICIANDO (LIGHTWEIGHT)")
    logger.info(f"Event: {json.dumps(event)}")
    logger.info("="*70)
    
    # Configurações (via environment variables ou event)
    ticker = os.environ.get('TICKER', 'PETR4')
    dataset = os.environ.get('DATASET', 'petr4')
    bucket = os.environ.get('S3_BUCKET')
    prefix = os.environ.get('S3_PREFIX', 'raw')
    days = int(os.environ.get('DAYS', '5'))  # Últimos 5 dias (para pegar novos)
    
    if not bucket:
        raise ValueError("S3_BUCKET environment variable not set")
    
    logger.info(f"Config: ticker={ticker}, dataset={dataset}, bucket={bucket}, days={days}")
    
    try:
        # 1. Fetch data
        raw_data = fetch_brapi_data(ticker, days)
        
        if not raw_data:
            logger.warning("No data fetched from API")
            return {
                "statusCode": 200,
                "body": json.dumps({
                    "message": "No new data available",
                    "files_uploaded": 0
                })
            }
        
        # 2. Transform
        records = prepare_dataframe(raw_data, ticker)
        logger.info(f"Processing {len(records)} records")
        
        # 3. Save to S3
        uploaded_files = save_to_s3_csv(records, bucket, prefix, dataset, ticker)
        
        logger.info("="*70)
        logger.info("LAMBDA SCRAPING B3 - CONCLUÍDO COM SUCESSO")
        logger.info(f"Files uploaded: {len(uploaded_files)}")
        logger.info("="*70)
        
        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Data scraped and uploaded successfully",
                "files_uploaded": len(uploaded_files),
                "s3_keys": uploaded_files
            })
        }
        
    except Exception as e:
        logger.error(f"Error in lambda_handler: {e}", exc_info=True)
        raise
