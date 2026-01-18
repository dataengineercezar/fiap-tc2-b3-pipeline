#!/usr/bin/env python3
"""
Script de ingestão de dados da B3 via yfinance
Atende Requisito R1: scrap de dados de ações/índices B3 (granularidade diária)
"""

import logging
import argparse
from datetime import datetime, timedelta
from pathlib import Path
import json
import sys

import yfinance as yf
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import boto3
from botocore.exceptions import ClientError

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class B3DataExtractor:
    """Extrator de dados da B3 usando yfinance"""
    
    def __init__(self, ticker: str, dataset_name: str = "petr4"):
        self.ticker = ticker
        self.dataset_name = dataset_name
        self.ticker_normalized = ticker.replace(".SA", "").lower()
        
    def extract_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """
        Extrai dados históricos do ticker
        
        Args:
            start_date: Data inicial (YYYY-MM-DD)
            end_date: Data final (YYYY-MM-DD)
            
        Returns:
            DataFrame com dados históricos
        """
        logger.info(f"Extraindo dados de {self.ticker} de {start_date} até {end_date}")
        
        try:
            ticker_obj = yf.Ticker(self.ticker)
            df = ticker_obj.history(start=start_date, end=end_date)
            
            if df.empty:
                logger.warning(f"Nenhum dado encontrado para {self.ticker}")
                return df
            
            # Reset index para ter Date como coluna
            df = df.reset_index()
            
            # Adicionar metadados
            df['ticker'] = self.ticker_normalized
            df['dataset'] = self.dataset_name
            df['extraction_timestamp'] = datetime.now().isoformat()
            
            # Criar colunas de particionamento
            df['date'] = pd.to_datetime(df['Date']).dt.date
            df['year'] = pd.to_datetime(df['Date']).dt.year
            df['month'] = pd.to_datetime(df['Date']).dt.month
            df['day'] = pd.to_datetime(df['Date']).dt.day
            
            logger.info(f"Extraídos {len(df)} registros")
            logger.info(f"Período: {df['date'].min()} até {df['date'].max()}")
            
            return df
            
        except Exception as e:
            logger.error(f"Erro ao extrair dados: {str(e)}")
            raise
    
    def save_local_json(self, df: pd.DataFrame, output_path: Path):
        """Salva dados localmente em JSON (para testes)"""
        output_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filepath = output_path / f"{self.ticker_normalized}_{timestamp}.json"
        
        df.to_json(filepath, orient='records', date_format='iso', indent=2)
        logger.info(f"Dados salvos em: {filepath}")
        
        return filepath
    
    def save_local_parquet(self, df: pd.DataFrame, output_path: Path, partition_cols: list = None):
        """
        Salva dados localmente em Parquet com particionamento
        
        Args:
            df: DataFrame com dados
            output_path: Caminho de saída
            partition_cols: Colunas para particionamento (padrão: ['year', 'month', 'day'])
        """
        if partition_cols is None:
            partition_cols = ['year', 'month', 'day']
        
        output_path = Path(output_path)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Criar estrutura de particionamento
        table = pa.Table.from_pandas(df)
        
        logger.info(f"Salvando em Parquet particionado por {partition_cols}")
        pq.write_to_dataset(
            table,
            root_path=str(output_path),
            partition_cols=partition_cols,
            existing_data_behavior='overwrite_or_ignore'
        )
        
        logger.info(f"Dados salvos em Parquet: {output_path}")
        return output_path
    
    def upload_to_s3(self, df: pd.DataFrame, bucket: str, prefix: str = "raw"):
        """
        Upload de dados para S3 em formato Parquet particionado
        Atende Requisito R2: dados brutos no S3 em Parquet com partição diária
        
        Args:
            df: DataFrame com dados
            bucket: Nome do bucket S3
            prefix: Prefixo (padrão: 'raw')
        """
        logger.info(f"Iniciando upload para s3://{bucket}/{prefix}")
        
        s3_client = boto3.client('s3')
        
        # Agrupar por data para salvar cada dia separadamente
        for date, group in df.groupby(['year', 'month', 'day']):
            year, month, day = date
            
            # Construir caminho S3 particionado
            s3_key = (
                f"{prefix}/dataset={self.dataset_name}/ticker={self.ticker_normalized}/"
                f"year={year}/month={month:02d}/day={day:02d}/data.parquet"
            )
            
            # Converter para Parquet em memória
            table = pa.Table.from_pandas(group)
            buffer = pa.BufferOutputStream()
            pq.write_table(table, buffer)
            
            # Upload
            try:
                s3_client.put_object(
                    Bucket=bucket,
                    Key=s3_key,
                    Body=buffer.getvalue().to_pybytes()
                )
                logger.info(f"Upload concluído: s3://{bucket}/{s3_key}")
                
            except ClientError as e:
                logger.error(f"Erro no upload para {s3_key}: {str(e)}")
                raise
        
        logger.info(f"Upload completo para s3://{bucket}/{prefix}")


def main():
    parser = argparse.ArgumentParser(description='Extrai dados da B3 via yfinance')
    parser.add_argument('--ticker', default='PETR4.SA', help='Ticker da ação (padrão: PETR4.SA)')
    parser.add_argument('--dataset', default='petr4', help='Nome do dataset (padrão: petr4)')
    parser.add_argument('--start-date', help='Data inicial (YYYY-MM-DD)')
    parser.add_argument('--end-date', help='Data final (YYYY-MM-DD)')
    parser.add_argument('--days', type=int, default=90, help='Últimos N dias (padrão: 90)')
    parser.add_argument('--output-dir', default='local_data', help='Diretório de saída local')
    parser.add_argument('--format', choices=['json', 'parquet'], default='parquet', help='Formato de saída')
    parser.add_argument('--s3-bucket', help='Bucket S3 (se não informado, salva local)')
    parser.add_argument('--s3-prefix', default='raw', help='Prefixo S3 (padrão: raw)')
    
    args = parser.parse_args()
    
    # Definir período
    if args.start_date and args.end_date:
        start_date = args.start_date
        end_date = args.end_date
    else:
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=args.days)).strftime('%Y-%m-%d')
    
    logger.info("="*60)
    logger.info("INICIANDO EXTRAÇÃO DE DADOS B3")
    logger.info(f"Ticker: {args.ticker}")
    logger.info(f"Dataset: {args.dataset}")
    logger.info(f"Período: {start_date} até {end_date}")
    logger.info("="*60)
    
    # Extrair dados
    extractor = B3DataExtractor(ticker=args.ticker, dataset_name=args.dataset)
    df = extractor.extract_data(start_date=start_date, end_date=end_date)
    
    if df.empty:
        logger.error("Nenhum dado extraído. Abortando.")
        sys.exit(1)
    
    # Mostrar resumo
    logger.info("\n" + "="*60)
    logger.info("RESUMO DOS DADOS EXTRAÍDOS")
    logger.info("="*60)
    logger.info(f"Total de registros: {len(df)}")
    logger.info(f"Colunas: {list(df.columns)}")
    logger.info(f"\nPrimeiras linhas:\n{df.head()}")
    logger.info(f"\nEstatísticas:\n{df[['Open', 'High', 'Low', 'Close', 'Volume']].describe()}")
    
    # Salvar dados
    if args.s3_bucket:
        # Upload para S3
        extractor.upload_to_s3(df=df, bucket=args.s3_bucket, prefix=args.s3_prefix)
    else:
        # Salvar localmente
        output_path = Path(args.output_dir)
        
        if args.format == 'json':
            filepath = extractor.save_local_json(df=df, output_path=output_path)
            logger.info(f"\n✅ Dados salvos em JSON: {filepath}")
        else:
            filepath = extractor.save_local_parquet(df=df, output_path=output_path)
            logger.info(f"\n✅ Dados salvos em Parquet: {filepath}")
    
    logger.info("\n" + "="*60)
    logger.info("EXTRAÇÃO CONCLUÍDA COM SUCESSO")
    logger.info("="*60)


if __name__ == '__main__':
    main()
