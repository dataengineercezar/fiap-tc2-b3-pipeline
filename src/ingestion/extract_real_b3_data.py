#!/usr/bin/env python3
"""
Extrator de dados REAIS da B3 usando APIs gratuitas brasileiras
Atende Requisito R1: scrap/extração de dados reais de ações da B3
"""

import logging
import argparse
from datetime import datetime, timedelta
from pathlib import Path
import sys
import time

import pandas as pd
import requests
from tenacity import retry, stop_after_attempt, wait_exponential
import pyarrow as pa
import pyarrow.parquet as pq
import boto3
from botocore.exceptions import ClientError

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RealB3DataExtractor:
    """Extrator de dados REAIS da B3 usando APIs gratuitas brasileiras"""
    
    def __init__(self, ticker: str = "PETR4", dataset_name: str = "petr4"):
        # Normalizar ticker (remover .SA se tiver)
        self.ticker = ticker.replace(".SA", "").upper()
        self.dataset_name = dataset_name
        self.ticker_normalized = self.ticker.lower()
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json'
        })
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _fetch_brapi_dev(self, range_period: str = "3mo") -> pd.DataFrame:
        """
        API BRAPI.DEV - API gratuita brasileira para dados da B3
        Documentação: https://brapi.dev/docs
        """
        logger.info("🇧🇷 Estratégia 1: BRAPI.DEV (API Brasileira Gratuita)")
        
        url = f"https://brapi.dev/api/quote/{self.ticker}"
        params = {
            'range': range_period,  # 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
            'interval': '1d',
            'fundamental': 'false'
        }
        
        logger.info(f"Requisição: {url} (range={range_period})")
        
        response = self.session.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if 'results' not in data or not data['results']:
            raise ValueError("Resposta vazia da API")
        
        stock_data = data['results'][0]
        
        if 'historicalDataPrice' not in stock_data:
            raise ValueError("Dados históricos não disponíveis")
        
        historical = stock_data['historicalDataPrice']
        
        if not historical:
            raise ValueError("Lista de dados históricos vazia")
        
        # Converter para DataFrame
        df = pd.DataFrame(historical)
        
        # Renomear colunas para padrão
        df = df.rename(columns={
            'date': 'Date',
            'open': 'Open',
            'high': 'High',
            'low': 'Low',
            'close': 'Close',
            'volume': 'Volume'
        })
        
        # Converter timestamp para datetime
        df['Date'] = pd.to_datetime(df['Date'], unit='s')
        
        # Adicionar Adj Close (igual Close para simplificar)
        df['Adj Close'] = df['Close']
        
        logger.info(f"✅ BRAPI.DEV: {len(df)} registros obtidos")
        
        return df
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _fetch_hgbrasil_finance(self) -> pd.DataFrame:
        """
        API HG Brasil Finance - Dados financeiros brasileiros
        Documentação: https://hgbrasil.com/status/finance
        """
        logger.info("🇧🇷 Estratégia 2: HG Brasil Finance API")
        
        url = "https://api.hgbrasil.com/finance/stock_price"
        params = {
            'key': 'free',  # Versão gratuita
            'symbol': self.ticker
        }
        
        logger.info(f"Requisição: {url}?symbol={self.ticker}")
        
        response = self.session.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if 'results' not in data or self.ticker not in data['results']:
            raise ValueError(f"Ticker {self.ticker} não encontrado na resposta")
        
        stock = data['results'][self.ticker]
        
        # API retorna apenas último preço, não histórico
        # Precisaríamos de chamadas múltiplas ou upgrade para versão paga
        raise ValueError("API HG Brasil não retorna histórico na versão gratuita")
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _fetch_yahoo_query_api(self, start_date: str, end_date: str) -> pd.DataFrame:
        """
        Yahoo Finance Query API v8 (alternativa)
        """
        logger.info("🌐 Estratégia 3: Yahoo Finance Query API v8")
        
        ticker_yf = f"{self.ticker}.SA"
        
        start_ts = int(pd.Timestamp(start_date).timestamp())
        end_ts = int(pd.Timestamp(end_date).timestamp())
        
        url = f"https://query2.finance.yahoo.com/v8/finance/chart/{ticker_yf}"
        params = {
            'period1': start_ts,
            'period2': end_ts,
            'interval': '1d',
            'events': 'history'
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        
        logger.info(f"Requisição: {url}")
        
        response = self.session.get(url, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if 'chart' not in data or 'result' not in data['chart']:
            raise ValueError("Formato de resposta inválido")
        
        result = data['chart']['result'][0]
        
        timestamps = result['timestamp']
        quotes = result['indicators']['quote'][0]
        
        df = pd.DataFrame({
            'Date': pd.to_datetime(timestamps, unit='s'),
            'Open': quotes['open'],
            'High': quotes['high'],
            'Low': quotes['low'],
            'Close': quotes['close'],
            'Volume': quotes['volume']
        })
        
        # Remover NaN
        df = df.dropna()
        
        # Adicionar Adj Close
        if 'adjclose' in result['indicators']:
            df['Adj Close'] = result['indicators']['adjclose'][0]['adjclose']
        else:
            df['Adj Close'] = df['Close']
        
        logger.info(f"✅ Yahoo Query API: {len(df)} registros obtidos")
        
        return df
    
    def extract_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """
        Extrai dados reais com múltiplas estratégias de fallback
        """
        logger.info(f"Extraindo dados REAIS de {self.ticker} ({start_date} até {end_date})")
        
        df = pd.DataFrame()
        
        # Calcular range para BRAPI
        days_diff = (pd.Timestamp(end_date) - pd.Timestamp(start_date)).days
        if days_diff <= 5:
            range_period = '5d'
        elif days_diff <= 30:
            range_period = '1mo'
        elif days_diff <= 90:
            range_period = '3mo'
        elif days_diff <= 180:
            range_period = '6mo'
        else:
            range_period = '1y'
        
        strategies = [
            ("BRAPI.DEV (API BR Gratuita)", lambda: self._fetch_brapi_dev(range_period)),
            ("Yahoo Query API v8", lambda: self._fetch_yahoo_query_api(start_date, end_date)),
        ]
        
        for strategy_name, strategy_func in strategies:
            try:
                logger.info(f"\n{'='*70}")
                logger.info(f"Tentando: {strategy_name}")
                logger.info(f"{'='*70}")
                
                df = strategy_func()
                
                if not df.empty:
                    logger.info(f"✅ SUCESSO com {strategy_name}")
                    logger.info(f"   {len(df)} registros extraídos")
                    break
                    
            except Exception as e:
                logger.warning(f"❌ {strategy_name} falhou: {str(e)}")
                time.sleep(2)  # Delay entre tentativas
                continue
        
        if df.empty:
            logger.error("\n" + "="*70)
            logger.error("❌ TODAS AS ESTRATÉGIAS DE EXTRAÇÃO FALHARAM")
            logger.error("="*70)
            logger.error("\nPossíveis soluções:")
            logger.error("1. Verifique sua conexão com a internet")
            logger.error("2. Tente novamente em alguns minutos (rate limit)")
            logger.error("3. Use VPN se estiver com bloqueio regional")
            logger.error("4. Considere APIs pagas: Alpha Vantage, IEX Cloud, Polygon.io")
            logger.error(f"5. Baixe CSV manualmente: https://br.investing.com/equities/petrobras-pn-historical-data")
            return df
        
        # Filtrar por período solicitado
        df = df[
            (df['Date'] >= pd.Timestamp(start_date)) & 
            (df['Date'] <= pd.Timestamp(end_date))
        ]
        
        # Ordenar por data
        df = df.sort_values('Date').reset_index(drop=True)
        
        # Adicionar metadados
        df['ticker'] = self.ticker_normalized
        df['dataset'] = self.dataset_name
        df['extraction_timestamp'] = datetime.now().isoformat()
        df['data_source'] = 'real_api_extraction'
        
        # Colunas de particionamento
        df['date'] = pd.to_datetime(df['Date']).dt.date
        df['year'] = pd.to_datetime(df['Date']).dt.year
        df['month'] = pd.to_datetime(df['Date']).dt.month
        df['day'] = pd.to_datetime(df['Date']).dt.day
        
        logger.info(f"\n{'='*70}")
        logger.info(f"✅ EXTRAÇÃO CONCLUÍDA COM SUCESSO")
        logger.info(f"{'='*70}")
        logger.info(f"Total de registros: {len(df)}")
        logger.info(f"Período: {df['date'].min()} até {df['date'].max()}")
        logger.info(f"Fonte: Dados REAIS da B3")
        
        return df
    
    def save_local_parquet(self, df: pd.DataFrame, output_path: Path):
        """Salva em Parquet particionado"""
        output_path = Path(output_path)
        output_path.mkdir(parents=True, exist_ok=True)
        
        table = pa.Table.from_pandas(df)
        
        pq.write_to_dataset(
            table,
            root_path=str(output_path),
            partition_cols=['year', 'month', 'day'],
            existing_data_behavior='overwrite_or_ignore'
        )
        
        logger.info(f"✅ Parquet salvo: {output_path}")
        return output_path
    
    def upload_to_s3(self, df: pd.DataFrame, bucket: str, prefix: str = "raw"):
        """Upload para S3"""
        logger.info(f"Upload para s3://{bucket}/{prefix}")
        
        s3_client = boto3.client('s3')
        
        for date, group in df.groupby(['year', 'month', 'day']):
            year, month, day = date
            
            s3_key = (
                f"{prefix}/dataset={self.dataset_name}/ticker={self.ticker_normalized}/"
                f"year={year}/month={month:02d}/day={day:02d}/data.parquet"
            )
            
            table = pa.Table.from_pandas(group)
            buffer = pa.BufferOutputStream()
            pq.write_table(table, buffer)
            
            s3_client.put_object(
                Bucket=bucket,
                Key=s3_key,
                Body=buffer.getvalue().to_pybytes()
            )
        
        logger.info(f"✅ Upload S3 completo")


def main():
    parser = argparse.ArgumentParser(description='Extrator de dados REAIS da B3')
    parser.add_argument('--ticker', default='PETR4', help='Ticker (sem .SA)')
    parser.add_argument('--dataset', default='petr4')
    parser.add_argument('--days', type=int, default=90)
    parser.add_argument('--start-date', help='YYYY-MM-DD')
    parser.add_argument('--end-date', help='YYYY-MM-DD')
    parser.add_argument('--output-dir', default='local_data/raw')
    parser.add_argument('--s3-bucket')
    parser.add_argument('--s3-prefix', default='raw')
    
    args = parser.parse_args()
    
    if args.start_date and args.end_date:
        start_date = args.start_date
        end_date = args.end_date
    else:
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=args.days)).strftime('%Y-%m-%d')
    
    logger.info("\n" + "="*70)
    logger.info("EXTRATOR DE DADOS REAIS DA B3")
    logger.info(f"Ticker: {args.ticker}")
    logger.info(f"Período: {start_date} até {end_date}")
    logger.info("="*70 + "\n")
    
    extractor = RealB3DataExtractor(ticker=args.ticker, dataset_name=args.dataset)
    df = extractor.extract_data(start_date=start_date, end_date=end_date)
    
    if df.empty:
        sys.exit(1)
    
    print(f"\n{df.head(10)}\n")
    print(f"Estatísticas:\n{df[['Open', 'High', 'Low', 'Close', 'Volume']].describe()}\n")
    
    if args.s3_bucket:
        extractor.upload_to_s3(df=df, bucket=args.s3_bucket, prefix=args.s3_prefix)
    else:
        extractor.save_local_parquet(df=df, output_path=Path(args.output_dir))


if __name__ == '__main__':
    main()
