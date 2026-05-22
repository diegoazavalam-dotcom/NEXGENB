#!/bin/bash
echo "Iniciando NexGen SCADA v7 en Docker..."

# Iniciar Gateway en segundo plano
echo "Arrancando Sensor Gateway..."
python gateway_service.py &
GATEWAY_PID=$!

# Esperar unos segundos para que el Gateway abra su puerto
sleep 3

# Iniciar App HMI Core en primer plano
echo "Arrancando Servidor HMI Core..."
python app.py &
APP_PID=$!

# Atrapar señales de terminación para matar ambos procesos
trap "kill $GATEWAY_PID $APP_PID" SIGINT SIGTERM EXIT

# Mantener vivo el contenedor esperando a los procesos
wait $APP_PID
wait $GATEWAY_PID
