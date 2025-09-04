#!/bin/bash

# Script para iniciar o Accumulator Bot em modo standalone
# Ideal para execução em VPS Linux

echo "========================================"
echo "  ACCUMULATOR BOT - MODO STANDALONE"
echo "========================================"
echo
echo "Iniciando Accumulator_Scalping_Bot..."
echo

# Verificar se o arquivo .env existe
if [ ! -f ".env" ]; then
    echo "⚠️  AVISO: Arquivo .env não encontrado!"
    echo "💡 Crie um arquivo .env com seu DERIV_TOKEN:"
    echo "   echo 'DERIV_TOKEN=seu_token_aqui' > .env"
    echo
fi

# Ativar ambiente virtual se existir
if [ -d "venv" ]; then
    echo "🔄 Ativando ambiente virtual..."
    source venv/bin/activate
elif [ -d ".venv" ]; then
    echo "🔄 Ativando ambiente virtual..."
    source .venv/bin/activate
else
    echo "⚠️  Ambiente virtual não encontrado. Usando Python global."
fi

# Verificar se o Python está disponível
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo "❌ Python não encontrado!"
        exit 1
    else
        PYTHON_CMD="python"
    fi
else
    PYTHON_CMD="python3"
fi

# Carregar variáveis de ambiente do arquivo .env
if [ -f ".env" ]; then
    echo "📋 Carregando variáveis de ambiente..."
    export $(cat .env | grep -v '^#' | xargs)
fi

# Verificar se o token está configurado
if [ -z "$DERIV_TOKEN" ]; then
    echo "❌ ERRO: DERIV_TOKEN não configurado!"
    echo "💡 Configure a variável de ambiente ou arquivo .env"
    exit 1
fi

echo "✅ Token configurado"
echo "🚀 Iniciando bot..."
echo

# Executar o bot standalone com tratamento de erros
$PYTHON_CMD accumulator_standalone.py

# Capturar código de saída
EXIT_CODE=$?

echo
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ Bot encerrado normalmente"
else
    echo "❌ Bot encerrado com erro (código: $EXIT_CODE)"
fi

echo "🏁 Execução finalizada"