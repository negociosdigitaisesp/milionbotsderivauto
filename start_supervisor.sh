#!/bin/bash
# Script de exemplo para executar o supervisor em background no Linux/Mac

echo "🚀 Iniciando Supervisor do Bot Trading System..."
echo "📁 Diretório atual: $(pwd)"
echo "📄 Verificando arquivos necessários..."

# Verificar se os arquivos existem
if [ ! -f "supervisor.py" ]; then
    echo "❌ Erro: supervisor.py não encontrado!"
    exit 1
fi

if [ ! -f "bot_trading_system.py" ]; then
    echo "❌ Erro: bot_trading_system.py não encontrado!"
    exit 1
fi

if [ ! -d "venv" ]; then
    echo "❌ Erro: Ambiente virtual 'venv' não encontrado!"
    echo "💡 Execute: python -m venv venv"
    exit 1
fi

echo "✅ Todos os arquivos necessários encontrados!"
echo ""

# Ativar ambiente virtual
echo "🔧 Ativando ambiente virtual..."
source venv/bin/activate

# Verificar se o Python do venv funciona
if ! venv/bin/python3 --version > /dev/null 2>&1; then
    echo "❌ Erro: Python do ambiente virtual não funciona!"
    exit 1
fi

echo "✅ Ambiente virtual ativo!"
echo ""

# Criar diretório de logs se não existir
mkdir -p logs

# Executar supervisor em background
echo "🚀 Iniciando supervisor em background..."
echo "📝 Logs serão salvos em: logs/supervisor.log"
echo "🛑 Para parar: kill \$(pgrep -f supervisor.py)"
echo ""

nohup python supervisor.py > logs/supervisor.log 2>&1 &
SUPERVISOR_PID=$!

echo "✅ Supervisor iniciado com PID: $SUPERVISOR_PID"
echo "📊 Para monitorar logs em tempo real:"
echo "   tail -f logs/supervisor.log"
echo ""
echo "🔍 Para verificar status:"
echo "   ps aux | grep supervisor.py"
echo ""
echo "🛑 Para parar o supervisor:"
echo "   kill $SUPERVISOR_PID"
echo ""

# Aguardar alguns segundos e verificar se ainda está rodando
sleep 3
if kill -0 $SUPERVISOR_PID 2>/dev/null; then
    echo "✅ Supervisor está rodando normalmente!"
    echo "📝 Últimas linhas do log:"
    echo "----------------------------------------"
    tail -n 5 logs/supervisor.log
    echo "----------------------------------------"
else
    echo "❌ Supervisor falhou ao iniciar!"
    echo "📝 Verificando logs de erro:"
    cat logs/supervisor.log
    exit 1
fi