@echo off
echo Iniciando Servidor Web HMI y Gateway Integrado...
start cmd /k "set PYTHONIOENCODING=utf-8 && venv\Scripts\activate && python app.py"

echo Sistema ZoLe Automatizacion Iniciado Correctamente.