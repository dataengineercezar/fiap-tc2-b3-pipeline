"""Lambda de scraping diário (B3).

- R1: extração diária (BRAPI)
- R2: ingestão em S3 RAW em formato Parquet com partição diária

Escreve Parquet diretamente em `raw/` para manter o pipeline simples e aderente ao Tech Challenge.
"""

import json
import logging
import os
from datetime import datetime
from io import BytesIO

import boto3
import pandas as pd
import requests

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def fetch_brapi_data(ticker: str, days: int = 30) -> list:
    """
    Busca dados da BRAPI.DEV API
    Retorna lista de dicts
    """
    logger.info(f"Fetching data for {ticker} from BRAPI.DEV")
    
    # BRAPI suporta: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
    if days <= 5:
        range_param = f"{days}d"
    elif days <= 30:
        range_param = "1mo"
    elif days <= 90:
        range_param = "3mo"
    elif days <= 180:
        range_param = "6mo"
    elif days <= 365:
        range_param = "1y"
    else:
        range_param = "max"
    
    # interval=1d necessário para obter historicalDataPrice
    url = f"https://brapi.dev/api/quote/{ticker}?range={range_param}&interval=1d"
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


def prepare_records(raw_data: list, ticker: str) -> list[dict]:
    """
    Transforma dados brutos em formato padronizado.
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


def save_to_s3_parquet(records: list[dict], bucket: str, dataset: str, ticker: str) -> list[str]:
    """Salva Parquet particionado por data em raw/ (R2)."""

    s3_client = boto3.client("s3")
    ticker_normalized = ticker.lower()

    by_date: dict[str, list[dict]] = {}
    for record in records:
        by_date.setdefault(record["Date"], []).append(record)

    uploaded_files: list[str] = []
    for date_str, group in by_date.items():
        dt = datetime.strptime(date_str, "%Y-%m-%d")

        df = pd.DataFrame(group)

        # Tipos consistentes (evita schema drift entre dias)
        df["Date"] = df["Date"].astype(str)
        for col_name in ["Open", "High", "Low", "Close", "Volume"]:
            df[col_name] = pd.to_numeric(df[col_name], errors="coerce").astype("float64")
        df["ticker"] = df["ticker"].astype(str)

        parquet_buffer = BytesIO()
        df.to_parquet(
            parquet_buffer,
            engine="pyarrow",
            compression="snappy",
            index=False,
        )
        parquet_buffer.seek(0)

        s3_key = (
            f"raw/dataset={dataset}/ticker={ticker_normalized}/"
            f"year={dt.year}/month={dt.month:02d}/day={dt.day:02d}/data.parquet"
        )

        s3_client.put_object(
            Bucket=bucket,
            Key=s3_key,
            Body=parquet_buffer.getvalue(),
            ContentType="application/x-parquet",
        )

        uploaded_files.append(s3_key)
        logger.info(f"Uploaded Parquet: s3://{bucket}/{s3_key} ({len(group)} records)")

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
    days = int(os.environ.get('DAYS', '30'))
    
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
        records = prepare_records(raw_data, ticker)
        logger.info(f"Processing {len(records)} records")
        
        # 3. Save to S3 (Parquet direto no RAW)
        uploaded_files = save_to_s3_parquet(records, bucket, dataset, ticker)
        
        logger.info("="*70)
        logger.info("LAMBDA SCRAPING B3 - CONCLUÍDO COM SUCESSO")
        logger.info(f"Files uploaded: {len(uploaded_files)}")
        logger.info("="*70)
        
        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Data scraped and uploaded to RAW (Parquet) successfully",
                "files_uploaded": len(uploaded_files),
                "s3_keys": uploaded_files
            })
        }
        
    except Exception as e:
        logger.error(f"Error in lambda_handler: {e}", exc_info=True)
        raise
