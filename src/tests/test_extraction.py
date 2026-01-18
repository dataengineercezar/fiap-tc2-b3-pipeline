"""
Testes básicos para o script de extração
"""

import pytest
from datetime import datetime, timedelta
import pandas as pd
from pathlib import Path
import sys

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ingestion.extract_b3_data import B3DataExtractor


def test_extractor_initialization():
    """Testa inicialização do extrator"""
    extractor = B3DataExtractor(ticker="PETR4.SA", dataset_name="petr4")
    
    assert extractor.ticker == "PETR4.SA"
    assert extractor.dataset_name == "petr4"
    assert extractor.ticker_normalized == "petr4"


def test_extract_data():
    """Testa extração de dados (smoke test)"""
    extractor = B3DataExtractor(ticker="PETR4.SA")
    
    # Extrair últimos 7 dias
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    
    df = extractor.extract_data(start_date=start_date, end_date=end_date)
    
    # Verificações básicas
    assert isinstance(df, pd.DataFrame)
    assert 'ticker' in df.columns
    assert 'dataset' in df.columns
    assert 'year' in df.columns
    assert 'month' in df.columns
    assert 'day' in df.columns
    
    if not df.empty:
        assert df['ticker'].iloc[0] == 'petr4'
        assert df['dataset'].iloc[0] == 'petr4'


def test_save_local_json(tmp_path):
    """Testa salvamento em JSON"""
    extractor = B3DataExtractor(ticker="PETR4.SA")
    
    # Criar DataFrame de teste
    test_data = {
        'Date': [datetime.now()],
        'Open': [30.0],
        'Close': [31.0],
        'ticker': ['petr4'],
        'dataset': ['petr4']
    }
    df = pd.DataFrame(test_data)
    
    # Salvar
    filepath = extractor.save_local_json(df=df, output_path=tmp_path)
    
    assert filepath.exists()
    assert filepath.suffix == '.json'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
