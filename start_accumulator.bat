@echo off
echo ========================================
echo  ACCUMULATOR BOT - MODO STANDALONE
echo ========================================
echo.
echo Iniciando Accumulator_Scalping_Bot...
echo.

REM Ativar ambiente virtual se existir
if exist "venv\Scripts\activate.bat" (
    echo Ativando ambiente virtual...
    call venv\Scripts\activate.bat
) else if exist ".venv\Scripts\activate.bat" (
    echo Ativando ambiente virtual...
    call .venv\Scripts\activate.bat
)

REM Executar o bot standalone
python accumulator_standalone.py

echo.
echo Bot encerrado. Pressione qualquer tecla para sair...
pause > nul