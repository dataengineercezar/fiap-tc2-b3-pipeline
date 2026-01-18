#!/bin/bash
# Upload Lambda deployment packages para S3

set -e

BUCKET="pos-tech-b3-pipeline-cezar-2026"
BUILD_DIR="/mnt/d/3_Estudos/FIAP_MLET/Fase2-BigDataArchitecture/TC2/build"

echo "=========================================="
echo "Upload Lambda Packages para S3"
echo "=========================================="

echo ""
echo "1. Fazendo upload de lambda_scraping.zip..."
aws s3 cp "$BUILD_DIR/lambda_scraping.zip" "s3://$BUCKET/lambda-deployments/lambda_scraping.zip"

echo ""
echo "✅ Upload concluído!"
echo ""
echo "Agora execute: terraform apply -auto-approve"
