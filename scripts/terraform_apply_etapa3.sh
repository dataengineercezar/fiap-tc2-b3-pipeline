#!/bin/bash
# Script para aplicar infraestrutura da ETAPA 3
# Lambda + EventBridge + IAM

set -e

cd /mnt/d/3_Estudos/FIAP_MLET/Fase2-BigDataArchitecture/TC2/terraform

echo "=========================================="
echo "TERRAFORM APPLY - ETAPA 3"
echo "IAM + Lambda + EventBridge"
echo "=========================================="

echo ""
echo "⚙️  Validando configuração..."
terraform validate

echo ""
echo "📋 Planejando mudanças..."
terraform plan -out=tfplan

echo ""
echo "🚀 Aplicando infraestrutura..."
echo "ATENÇÃO: Isso vai criar recursos na AWS"
read -p "Deseja continuar? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "❌ Cancelado pelo usuário"
    exit 1
fi

terraform apply tfplan

echo ""
echo "=========================================="
echo "✅ INFRAESTRUTURA APLICADA COM SUCESSO!"
echo "=========================================="
echo ""
echo "📊 Outputs:"
terraform output

echo ""
echo "🔍 Próximos passos:"
echo "1. Verificar CloudWatch Logs das Lambdas"
echo "2. Testar invoke manual da Lambda de scraping"
echo "3. Aguardar execução agendada (19h BRT)"
echo "4. Validar novos arquivos no S3"
