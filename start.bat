@echo off
echo Iniciando NexGen SCADA v7 (Arquitectura de Microservicios)...

echo Iniciando Gateway S7 (Puerto 5006)...
start cmd /k "set PYTHONIOENCODING=utf-8 && venv\Scripts\activate && python gateway_service.py"

echo Esperando a que el Gateway levante...
timeout /t 3 /nobreak >nul

echo Iniciando Servidor Web Core HMI (Puerto 5005 TLS)...
start cmd /k "set PYTHONIOENCODING=utf-8 && venv\Scripts\activate && python app.py"

echo Sistema Iniciado Correctamente.
echo POR FAVOR, ACCEDE DESDE TU NAVEGADOR USANDO: https://localhost:5005
pause