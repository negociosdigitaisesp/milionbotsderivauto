@echo off
REM Script de exemplo para executar o supervisor em background no Windows

echo 🚀 Iniciando Supervisor do Bot Trading System...
echo 📁 Diretório atual: %CD%
echo 📄 Verificando arquivos necessários...

REM Verificar se os arquivos existem
if not exist "supervisor.py" (
    echo ❌ Erro: supervisor.py não encontrado!
    pause
    exit /b 1
)

if not exist "bot_trading_system.py" (
    echo ❌ Erro: bot_trading_system.py não encontrado!
    pause
    exit /b 1
)

if not exist "venv" (
    echo ❌ Erro: Ambiente virtual 'venv' não encontrado!
    echo 💡 Execute: python -m venv venv
    pause
    exit /b 1
)

echo ✅ Todos os arquivos necessários encontrados!
echo.

REM Verificar se o Python do venv funciona
venv\Scripts\python.exe --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Erro: Python do ambiente virtual não funciona!
    pause
    exit /b 1
)

echo ✅ Ambiente virtual verificado!
echo.

REM Criar diretório de logs se não existir
if not exist "logs" mkdir logs

REM Executar supervisor em background
echo 🚀 Iniciando supervisor em background...
echo 📝 Logs serão salvos em: logs\supervisor.log
echo 🛑 Para parar: Feche a janela do supervisor ou use Ctrl+C
echo.

REM Iniciar supervisor em nova janela
start "Bot Trading Supervisor" /min cmd /c "venv\Scripts\python.exe supervisor.py > logs\supervisor.log 2>&1"

echo ✅ Supervisor iniciado em nova janela!
echo 📊 Para monitorar logs:
echo    type logs\supervisor.log
echo.
echo 📝 Para monitorar logs em tempo real:
echo    powershell Get-Content logs\supervisor.log -Wait
echo.
echo 🔍 Para verificar se está rodando:
echo    tasklist ^| findstr python
echo.

REM Aguardar alguns segundos e verificar logs
timeout /t 3 /nobreak >nul
if exist "logs\supervisor.log" (
    echo ✅ Supervisor iniciado com sucesso!
    echo 📝 Últimas linhas do log:
    echo ----------------------------------------
    powershell "Get-Content logs\supervisor.log | Select-Object -Last 5"
    echo ----------------------------------------
) else (
    echo ❌ Supervisor pode ter falhado ao iniciar!
    echo 💡 Verifique se não há erros no ambiente virtual
)

echo.
echo 🎯 Supervisor está rodando em background!
echo 📊 Use o dashboard para monitorar: http://localhost:8506
pause