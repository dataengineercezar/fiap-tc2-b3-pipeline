#!/usr/bin/env python3
"""
Processador de CSV local da B3 (fallback quando yfinance não funciona)
Atende Requisito R1: dados de ações B3 com granularidade diária
"""

import logging
import argparse
from datetime import datetime
from pathlib import Path
import sys

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import boto3
from botocore.exceptions import ClientError

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CSVProcessor:
    """Processador de CSV local baixado do Yahoo Finance"""
    
    def __init__(self, ticker: str = "PETR4.SA", dataset_name: str = "petr4"):
        self.ticker = ticker
        self.dataset_name = dataset_name
        self.ticker_normalized = ticker.replace(".SA", "").lower()
    
    def process_csv(self, csv_path: Path) -> pd.DataFrame:
        """
        Processa CSV baixado do Yahoo Finance
        
        Args:
            csv_path: Caminho para o arquivo CSV
            
        Returns:
            DataFrame processado com metadados e partições
        """
        logger.info(f"Processando CSV: {csv_path}")
        
        if not csv_path.exists():
            logger.error(f"Arquivo não encontrado: {csv_path}")
            raise FileNotFoundError(f"CSV não encontrado: {csv_path}")
        
        # Ler CSV
        df = pd.read_csv(csv_path)
        
        # Verificar colunas esperadas
        required_cols = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            logger.error(f"Colunas faltando no CSV: {missing_cols}")
            raise ValueError(f"CSV inválido. Colunas faltando: {missing_cols}")
        
        # Remover linhas com null
        df = df.dropna()
        
        # Adicionar metadados
        df['ticker'] = self.ticker_normalized
        df['dataset'] = self.dataset_name
        df['extraction_timestamp'] = datetime.now().isoformat()
        df['data_source'] = 'yahoo_finance_manual_csv'
        
        # Criar colunas de particionamento
        df['date'] = pd.to_datetime(df['Date']).dt.date
        df['year'] = pd.to_datetime(df['Date']).dt.year
        df['month'] = pd.to_datetime(df['Date']).dt.month
        df['day'] = pd.to_datetime(df['Date']).dt.day
        
        logger.info(f"✅ CSV processado com sucesso: {len(df)} registros")
        logger.info(f"Período: {df['date'].min()} até {df['date'].max()}")
        
        return df
    
    def save_json(self, df: pd.DataFrame, output_path: Path):
        """Salva em JSON"""
        output_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filepath = output_path / f"{self.ticker_normalized}_{timestamp}.json"
        
        df.to_json(filepath, orient='records', date_format='iso', indent=2)
        logger.info(f"Dados salvos em JSON: {filepath}")
        
        return filepath
    
    def save_parquet(self, df: pd.DataFrame, output_path: Path, partition_cols: list = None):
        """Salva em Parquet particionado"""
        if partition_cols is None:
            partition_cols = ['year', 'month', 'day']
        
        output_path = Path(output_path)
        output_path.mkdir(parents=True, exist_ok=True)
        
        table = pa.Table.from_pandas(df)
        
        logger.info(f"Salvando em Parquet particionado por {partition_cols}")
        pq.write_to_dataset(
            table,
            root_path=str(output_path),
            partition_cols=partition_cols,
            existing_data_behavior='overwrite_or_ignore'
        )
        
        logger.info(f"✅ Dados salvos em Parquet: {output_path}")
        return output_path
    
    def upload_to_s3(self, df: pd.DataFrame, bucket: str, prefix: str = "raw"):
        """Upload para S3 em Parquet particionado"""
        logger.info(f"Iniciando upload para s3://{bucket}/{prefix}")
        
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
            
            try:
                s3_client.put_object(
                    Bucket=bucket,
                    Key=s3_key,
                    Body=buffer.getvalue().to_pybytes()
                )
                logger.info(f"Upload concluído: s3://{bucket}/{s3_key}")
            except ClientError as e:
                logger.error(f"Erro no upload: {str(e)}")
                raise
        
        logger.info(f"✅ Upload completo para s3://{bucket}/{prefix}")


def main():
    parser = argparse.ArgumentParser(
        description='Processa CSV local da B3 (baixado manualmente do Yahoo Finance)'
    )
    parser.add_argument('--csv-file', required=True, help='Caminho para o CSV baixado')
    parser.add_argument('--ticker', default='PETR4.SA', help='Ticker da ação')
    parser.add_argument('--dataset', default='petr4', help='Nome do dataset')
    parser.add_argument('--output-dir', default='local_data', help='Diretório de saída')
    parser.add_argument('--format', choices=['json', 'parquet'], default='parquet')
    parser.add_argument('--s3-bucket', help='Bucket S3 (opcional)')
    parser.add_argument('--s3-prefix', default='raw', help='Prefixo S3')
    
    args = parser.parse_args()
    
    logger.info("="*70)
    logger.info("PROCESSANDO CSV LOCAL DA B3")
    logger.info(f"CSV: {args.csv_file}")
    logger.info(f"Ticker: {args.ticker}")
    logger.info(f"Dataset: {args.dataset}")
    logger.info("="*70)
    
    # Processar CSV
    processor = CSVProcessor(ticker=args.ticker, dataset_name=args.dataset)
    df = processor.process_csv(csv_path=Path(args.csv_file))
    
    if df.empty:
        logger.error("CSV vazio ou inválido. Abortando.")
        sys.exit(1)
    
    # Mostrar resumo
    logger.info("\n" + "="*70)
    logger.info("RESUMO DOS DADOS")
    logger.info("="*70)
    logger.info(f"Total de registros: {len(df)}")
    logger.info(f"Colunas: {list(df.columns)}")
    logger.info(f"\nPrimeiras linhas:\n{df.head()}")
    logger.info(f"\nEstatísticas:\n{df[['Open', 'High', 'Low', 'Close', 'Volume']].describe()}")
    
    # Salvar
    if args.s3_bucket:
        processor.upload_to_s3(df=df, bucket=args.s3_bucket, prefix=args.s3_prefix)
    else:
        output_path = Path(args.output_dir)
        
        if args.format == 'json':
            filepath = processor.save_json(df=df, output_path=output_path)
            logger.info(f"\n✅ JSON: {filepath}")
        else:
            filepath = processor.save_parquet(df=df, output_path=output_path)
            logger.info(f"\n✅ Parquet: {filepath}")
    
    logger.info("\n" + "="*70)
    logger.info("✅ PROCESSAMENTO CONCLUÍDO COM SUCESSO")
    logger.info("="*70)


if __name__ == '__main__':
    main()
