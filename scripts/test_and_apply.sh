#!/bin/bash
# Testar e aplicar após adicionar permissões

set -e

cd /mnt/d/3_Estudos/FIAP_MLET/Fase2-BigDataArchitecture/TC2/terraform

echo "Testando permissões IAM..."
aws iam list-roles --max-items 1 > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo "✅ Permissões IAM OK!"
    echo ""
    echo "Aplicando Terraform..."
    terraform apply -auto-approve
else
    echo "❌ Ainda sem permissões IAM"
    echo "Adicione IAMFullAccess ao usuário cezar-cli no console AWS"
    exit 1
fi
