#!/bin/bash
# Script para empacotar Lambda Trigger Glue (sem dependências pesadas)

set -e

echo "=========================================="
echo "Empacotando Lambda Trigger Glue"
echo "=========================================="

# Configurações
LAMBDA_NAME="lambda_trigger_glue"
LAMBDA_DIR="src/lambda"
BUILD_DIR="build/lambda_trigger_glue"
OUTPUT_ZIP="build/lambda_trigger_glue.zip"

# Limpar build anterior
rm -rf "$BUILD_DIR"
rm -f "$OUTPUT_ZIP"

# Criar diretório de build
mkdir -p "$BUILD_DIR"

echo "1. Copiando código Lambda..."
cp "$LAMBDA_DIR/lambda_trigger_glue.py" "$BUILD_DIR/"

echo "2. Criando ZIP (sem dependências externas - usa boto3 built-in)..."
cd "$BUILD_DIR"
zip -r "../$(basename "$OUTPUT_ZIP")" . -q
cd -

# Verificar tamanho
SIZE=$(du -h "$OUTPUT_ZIP" | cut -f1)
echo ""
echo "✅ Lambda empacotado com sucesso!"
echo "📦 Arquivo: $OUTPUT_ZIP"
echo "📏 Tamanho: $SIZE"
echo ""
