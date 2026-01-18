# Tech Challenge Fase 2 - Pipeline Batch B3 (PETR4)

## Arquitetura
Pipeline de dados batch para ingestão, transformação e análise de ações da B3 (PETR4.SA).

### Serviços AWS
- **S3**: Raw (JSON/Parquet) + Refined (Parquet particionado)
- **Lambda**: Trigger para iniciar Glue Job
- **Glue**: ETL (transformações obrigatórias)
- **Glue Catalog**: Metadados + tabela
- **Athena**: Queries SQL analíticas
- **EventBridge**: Agendamento diário (opcional)

## Requisitos Atendidos
- [R1] Extração diária PETR4.SA via yfinance
- [R2] Ingestão S3 RAW em Parquet com partição diária
- [R3] S3 Event → Lambda → Glue Job
- [R4] Lambda Python iniciando Glue
- [R5] Transformações Glue (agregação + rename + cálculo temporal)
- [R6] Dados refined particionados por data e ticker
- [R7] Catalogação automática no Glue Catalog
- [R8] Consultas SQL via Athena

## Setup Local
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```