#!/bin/bash
# Script para empacotar Lambda com dependências

set -e

echo "=========================================="
echo "Empacotando Lambda de Scraping"
echo "=========================================="

# Configurações
LAMBDA_NAME="lambda_scraping"
LAMBDA_DIR="src/lambda"
BUILD_DIR="build/lambda_scraping"
OUTPUT_ZIP="build/lambda_scraping.zip"

# Limpar build anterior
rm -rf "$BUILD_DIR"
rm -f "$OUTPUT_ZIP"

# Criar diretório de build
mkdir -p "$BUILD_DIR"

echo "1. Copiando código Lambda..."
cp "$LAMBDA_DIR/lambda_scraping.py" "$BUILD_DIR/"

echo "2. Instalando dependências no build..."
pip install \
    pandas==2.2.0 \
    pyarrow==15.0.0 \
    requests==2.31.0 \
    -t "$BUILD_DIR/" \
    --platform manylinux2014_x86_64 \
    --only-binary=:all: \
    --python-version 3.12

echo "3. Removendo arquivos desnecessários..."
cd "$BUILD_DIR"
find . -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete
find . -name "*.dist-info" -type d -exec rm -rf {} + 2>/dev/null || true
cd -

echo "4. Criando ZIP..."
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
echo "Para deploy:"
echo "  terraform apply -var-file=environments/dev/terraform.tfvars"
