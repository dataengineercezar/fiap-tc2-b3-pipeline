# 📋 Guia de Validação - ETAPA 3 no Console AWS

**Região:** São Paulo (sa-east-1)  
**Data:** 18/01/2026

---

## ✅ **1. IAM ROLES**

**Link:** https://console.aws.amazon.com/iam/home#/roles

### O que verificar:

1. **Role: b3-pipeline-lambda-scraping-dev**
   - ✅ Status: Ativo
   - ✅ Trusted Entity: Lambda (lambda.amazonaws.com)
   - ✅ Policies:
     - `AWSLambdaBasicExecutionRole` (AWS Managed)
     - `lambda-s3-access` (Inline Policy)
   - ✅ Inline Policy `lambda-s3-access` deve ter:
     - Actions: `s3:PutObject`, `s3:GetObject`, `s3:ListBucket`, `s3:PutObjectAcl`
     - Resource: `arn:aws:s3:::pos-tech-b3-pipeline-cezar-2026/*`

2. **Role: b3-pipeline-lambda-trigger-glue-dev**
   - ✅ Status: Ativo
   - ✅ Trusted Entity: Lambda
   - ✅ Policies:
     - `AWSLambdaBasicExecutionRole` (AWS Managed)
     - `lambda-start-glue` (Inline Policy)
   - ✅ Inline Policy `lambda-start-glue` deve ter:
     - Actions: `glue:StartJobRun`, `glue:GetJobRun`, `glue:GetJobRuns`
     - Resource: `*`

---

## ✅ **2. LAMBDA FUNCTIONS**

**Link:** https://console.aws.amazon.com/lambda/home?region=sa-east-1#/functions

### O que verificar:

1. **Function: b3-pipeline-scraping-dev**
   - ✅ Runtime: Python 3.12
   - ✅ Memory: 512 MB
   - ✅ Timeout: 5 minutes
   - ✅ Handler: `lambda_scraping.lambda_handler`
   - ✅ Execution Role: `b3-pipeline-lambda-scraping-dev`
   - ✅ Environment Variables:
     - `TICKER` = `petr4`
     - `DATASET` = `petr4`
     - `S3_BUCKET` = `pos-tech-b3-pipeline-cezar-2026`
     - `S3_PREFIX` = `raw`
     - `DAYS` = `5`
   - ✅ Code Source: Loaded from S3 (lambda-deployments/lambda_scraping.zip)
   - ✅ Code Size: ~62.75 MB (pandas + pyarrow)

   **Testar:**
   - Clique em "Test" tab
   - Configure test event (deixe vazio `{}`)
   - Execute e verifique:
     - Status: 200
     - Response: `"message": "Data scraped and uploaded successfully"`
     - Duration: ~1-3 segundos

2. **Function: b3-pipeline-trigger-glue-dev**
   - ✅ Runtime: Python 3.12
   - ✅ Memory: 256 MB
   - ✅ Timeout: 1 minute
   - ✅ Handler: `lambda_trigger_glue.lambda_handler`
   - ✅ Execution Role: `b3-pipeline-lambda-trigger-glue-dev`
   - ✅ Environment Variables:
     - `GLUE_JOB_NAME` = `b3-pipeline-etl-dev`
   - ✅ Code Size: ~4 KB (sem dependências externas)
   - ⚠️ **Nota:** Ainda não testável (precisa do Glue Job - Etapa 4)

---

## ✅ **3. CLOUDWATCH LOGS**

**Link:** https://console.aws.amazon.com/cloudwatch/home?region=sa-east-1#logsV2:log-groups

### O que verificar:

1. **Log Group: /aws/lambda/b3-pipeline-scraping-dev**
   - ✅ Retention: 7 days
   - ✅ Log Streams: Deve haver pelo menos 1 stream do teste manual
   - ✅ No último log stream, verificar:
     ```
     LAMBDA SCRAPING B3 - INICIANDO
     Config: ticker=petr4, dataset=petr4, bucket=pos-tech-b3-pipeline-cezar-2026, days=5
     Fetching data for petr4 from BRAPI.DEV
     Fetched 5 records
     Processing 1 records for 2026-01-16
     Uploaded: s3://.../raw/dataset=petr4/ticker=petr4/year=2026/month=01/day=16/data.parquet
     LAMBDA SCRAPING B3 - CONCLUÍDO COM SUCESSO
     Files uploaded: 1
     ```

2. **Log Group: /aws/lambda/b3-pipeline-trigger-glue-dev**
   - ✅ Retention: 7 days
   - ⚠️ Sem logs ainda (será acionado por S3 Event quando Glue Job estiver pronto)

---

## ✅ **4. EVENTBRIDGE SCHEDULE**

**Link:** https://console.aws.amazon.com/events/home?region=sa-east-1#/rules

### O que verificar:

1. **Rule: b3-pipeline-scraping-schedule-dev**
   - ✅ Status: **ENABLED** (importante!)
   - ✅ Event Bus: default
   - ✅ Schedule Expression: `cron(0 22 ? * MON-FRI *)`
     - Tradução: Segunda a Sexta às 22:00 UTC = **19:00 BRT**
     - Horário após fechamento da B3 (18h)
   - ✅ Target: Lambda function `b3-pipeline-scraping-dev`
   - ✅ Description: "Aciona Lambda de scraping diariamente após fechamento B3"

   **Próximas Execuções:**
   - Próxima segunda-feira às 19h BRT
   - Execuções automáticas em dias úteis

---

## ✅ **5. S3 BUCKET - VALIDAR ESTRUTURA**

**Link:** https://s3.console.aws.amazon.com/s3/buckets/pos-tech-b3-pipeline-cezar-2026?region=sa-east-1

### O que verificar:

1. **Diretório: lambda-deployments/**
   - ✅ `lambda_scraping.zip` (~62.75 MB)

2. **Diretório: raw/dataset=petr4/ticker=petr4/**
   - ✅ Estrutura de partições: `year=YYYY/month=MM/day=DD/`
   - ✅ Pelo menos 61 arquivos Parquet:
     - 60 arquivos antigos (upload manual da Etapa 2)
     - 1 arquivo novo (Lambda test: year=2026/month=01/day=16/data.parquet)
   - ✅ Tamanho médio: ~11-12 KB por arquivo

   **Validar arquivo específico:**
   - Path: `raw/dataset=petr4/ticker=petr4/year=2026/month=01/day=16/data.parquet`
   - Size: ~11.6 KB
   - Last Modified: 18/01/2026 16:53 (horário do teste manual)

---

## ✅ **6. TERRAFORM STATE**

**Verificar via CLI (opcional):**

```bash
wsl bash -c "cd /mnt/d/3_Estudos/FIAP_MLET/Fase2-BigDataArchitecture/TC2/terraform && terraform state list"
```

**Deve listar 20 recursos:**
- 6 recursos S3 (da Etapa 2)
- 6 recursos IAM (2 roles + 2 policies + 2 attachments)
- 6 recursos Lambda (2 functions + 2 log groups + 2 permissions)
- 3 recursos EventBridge (1 rule + 1 target + 1 permission)

---

## 📊 **RESUMO DE VALIDAÇÃO**

| Serviço | Recursos | Status | Testado |
|---------|----------|--------|---------|
| **IAM** | 2 roles + 4 policies | ✅ Criado | ✅ Validado |
| **Lambda** | 2 functions | ✅ Criado | ✅ 1 testada (scraping) |
| **CloudWatch Logs** | 2 log groups | ✅ Criado | ✅ Logs visíveis |
| **EventBridge** | 1 schedule rule | ✅ ENABLED | ⏳ Aguardando próxima execução |
| **S3** | 61 arquivos Parquet | ✅ Criado | ✅ Validado |

---

## 🚨 **PONTOS DE ATENÇÃO**

1. **EventBridge Schedule:** 
   - Verifique que está **ENABLED**
   - Próxima execução: Segunda-feira 19h BRT
   - Se quiser testar antes, desabilite a rule e invoque a Lambda manualmente

2. **Lambda Scraping:**
   - Sempre busca últimos 5 dias da API
   - Filtra apenas o dia mais recente para evitar duplicatas
   - Se executar no final de semana, buscará última sexta-feira

3. **Lambda Trigger Glue:**
   - Ainda não funcional (aguarda Glue Job - Etapa 4)
   - Não gera erro, apenas não tem job para acionar

4. **Custos AWS:**
   - EventBridge: ~$1/milhão de invocações
   - Lambda scraping: ~$0.000016/execução (5x/semana)
   - CloudWatch Logs: Grátis (dentro do Free Tier)
   - **Estimativa mensal:** < $1 USD

---

## ✅ **CHECKLIST FINAL**

Antes de avançar para Etapa 4, confirme:

- [ ] Ambas as IAM Roles criadas e com permissões corretas
- [ ] Lambda `b3-pipeline-scraping-dev` testada com sucesso
- [ ] CloudWatch Logs com mensagens de sucesso
- [ ] EventBridge Schedule **ENABLED** e configurado corretamente
- [ ] Novo arquivo Parquet no S3 (2026-01-16)
- [ ] Terraform state consistente (20 recursos)

**Após validação, podemos seguir para ETAPA 4: Glue ETL Job!** 🚀
