@echo off
TITLE SCADA NEXGEN - WATCHDOG
COLOR 0A

:INICIO
CLS
ECHO ---------------------------------------------------
ECHO    INICIANDO SISTEMA SCADA - NO CERRAR ESTA VENTANA
ECHO ---------------------------------------------------
date /t 
time /t
ECHO.

:: Activa tu entorno virtual (ajusta la ruta si es necesario)
:: Si no usas entorno virtual, comenta la siguiente linea
call venv\Scripts\activate

:: Inicia el servidor de producción
python server.py

:: Si el programa se cierra (crash), espera 5 segundos y reinicia
ECHO.
ECHO ⚠️ EL SISTEMA SE DETUVO. REINICIANDO EN 5 SEGUNDOS...
ECHO ⚠️ REGISTRANDO INCIDENTE EN LOG DEL SISTEMA...
timeout /t 5
GOTO INICIO