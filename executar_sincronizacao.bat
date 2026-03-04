@echo off
REM Script de execucao da sincronizacao agendada
REM Configurado para rodar via Task Scheduler do Windows

cd /d "C:\Users\Rafael\Desktop\Projeto comissoes"

REM Ativar ambiente virtual se existir
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

REM Executar sincronizacao
python sincronizacao_agendada.py

REM Desativar ambiente virtual
if exist "venv\Scripts\deactivate.bat" (
    call deactivate
)
