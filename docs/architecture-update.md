# Atualização Arquitetura - Lambda Dupla

## Problema Identificado
**Requisito 2 violado**: dados brutos em JSON ao invés de Parquet

> "os dados brutos devem ser ingeridos no s3 em **formato parquet** com partição diária"

## Solução Implementada: Arquitetura Lambda Dupla

```
┌──────────────────────────────────────────────────────────────────┐
│                    PIPELINE COMPLETO B3                          │
└──────────────────────────────────────────────────────────────────┘

1️⃣  LAMBDA SCRAPING (Lightweight - 1MB)
    ├─ Scraping BRAPI API
    ├─ Transforma em JSON
    └─ S3: temp/dataset=/ticker=/year=/month=/day=/data.json
         │
         └─▶ S3 Event Notification
              │
2️⃣  LAMBDA CONVERTER (com pandas+fastparquet Layer)              │
    ├─ Lê JSON de temp/                                         ◀─┘
    ├─ Converte para DataFrame
    ├─ Gera Parquet com fastparquet
    ├─ Upload S3: raw/.../*.parquet ✅ REQUISITO 2
    └─ Deleta JSON temp/ (opcional)
         │
         └─▶ S3 Event Notification
              │
3️⃣  LAMBDA TRIGGER (Existente)                                   │
    └─ Inicia Glue Job                                          ◀─┘
         │
4️⃣  GLUE JOB ETL                                                 │
    ├─ Lê Parquet de raw/                                       ◀─┘
    ├─ Aplica R5-A: Agrupamentos/Sumarização
    ├─ Aplica R5-B: Renomear colunas
    ├─ Aplica R5-C: Cálculos com data (MA, %)
    └─ S3: refined/.../*.parquet ✅ REQUISITO 6
         │
5️⃣  GLUE CRAWLER                                                 │
    └─ Cataloga tabela refined ✅ REQUISITO 7                   ◀─┘
         │
6️⃣  ATHENA                                                        │
    └─ SQL queries ✅ REQUISITO 8                                ◀─┘
```

## Benefícios

### ✅ Compliance Total
- **R2**: Dados brutos em Parquet no raw/
- **R3**: S3 aciona Lambda (duas vezes: temp→Converter, raw→Trigger)
- **R4**: Lambda inicia Glue Job

### ✅ Técnico
- **Tamanho**: Lambda Scraping = 1MB (requests apenas)
- **Flexibilidade**: Lambda Converter pode usar Layer (pandas isolado)
- **Manutenibilidade**: Separation of concerns
- **Performance**: Fastparquet rápido e leve (1.8MB vs PyArrow 47MB)

### ✅ Operacional
- **Sem limites AWS**: Cada Lambda < 250MB
- **Escalável**: Processa múltiplos JSONs em paralelo
- **Resiliente**: Retry automático por Lambda
- **Custo**: Lambda < 1s execution (grátis no free tier)

## Componentes

### Lambda Scraping
- **Código**: `src/lambda/lambda_scraping.py`
- **Deploy**: `lambda_minimal.zip` (1.05MB)
- **Runtime**: Python 3.12
- **Memória**: 512 MB
- **Timeout**: 60s
- **Output**: `s3://bucket/temp/dataset=/ticker=/year=/month=/day=/data.json`

### Lambda Converter
- **Código**: `src/lambda/lambda_converter.py`
- **Deploy**: ZIP com pandas+fastparquet
- **Runtime**: Python 3.12
- **Memória**: 512 MB
- **Timeout**: 60s
- **Trigger**: S3 PUT em `temp/*`
- **Output**: `s3://bucket/raw/dataset=/ticker=/year=/month=/day=/data.parquet`

### Lambda Trigger (Existente)
- Já implementado anteriormente
- Trigger**: S3 PUT em `raw/*`
- **Ação**: Inicia Glue Job

## Deployment

```bash
# 1. Deploy Lambda Scraping (atualizada para temp/)
cd src/lambda
zip -j lambda_scraping_update.zip lambda_scraping.py
aws lambda update-function-code \
  --function-name b3-pipeline-scraping-dev \
  --zip-file fileb://lambda_scraping_update.zip \
  --region sa-east-1

# 2. Build Lambda Converter
cd lambda_converter
cp ../lambda_converter.py .
zip -r9 ../lambda_converter.zip .
cd ..

# 3. Create Lambda Converter
aws lambda create-function \
  --function-name b3-pipeline-converter-dev \
  --runtime python3.12 \
  --role arn:aws:iam::ACCOUNT:role/b3-pipeline-lambda-role-dev \
  --handler lambda_converter.lambda_handler \
  --zip-file fileb://lambda_converter.zip \
  --timeout 60 \
  --memory-size 512 \
  --region sa-east-1

# 4. Configure S3 Event: temp/ → Lambda Converter
aws s3api put-bucket-notification-configuration \
  --bucket pos-tech-b3-pipeline-cezar-2026 \
  --notification-configuration file://s3_notification_temp.json

# 5. Test pipeline
aws lambda invoke \
  --function-name b3-pipeline-scraping-dev \
  --region sa-east-1 \
  /tmp/scraping.json
```

## Validação R2

```bash
# Verificar Parquet em raw/
aws s3 ls s3://pos-tech-b3-pipeline-cezar-2026/raw/dataset=petr4/ --recursive | grep parquet

# Download e inspeção
aws s3 cp s3://.../data.parquet /tmp/test.parquet
python3 -c "
import pandas as pd
df = pd.read_parquet('/tmp/test.parquet')
print('✅ Formato: Parquet')
print(f'✅ Registros: {len(df)}')
print(f'✅ Schema: {df.dtypes.to_dict()}')
"
```

## Status
- ✅ Lambda Converter criado
- ✅ Lambda Scraping atualizado (temp/ ao invés de raw/)
- ⏳ Instalando pandas+fastparquet
- ⏳ Build Lambda Converter ZIP
- ⏳ Deploy Lambda Converter
- ⏳ Configurar S3 Event notifications
- ⏳ Teste end-to-end
