from waitress import serve
from app import app
import socket

# Obtener la IP real de la máquina para mostrarla en consola
hostname = socket.gethostname()
local_ip = socket.gethostbyname(hostname)

print("---------------------------------------------------------")
print(f"🏭 SCADA NEXGEN SERVER - MODO PRODUCCIÓN INDUSTRIAL")
print(f"📡 Escuchando en: http://{local_ip}:5000")
print("---------------------------------------------------------")

# Lanzamos el servidor con 6 hilos de procesamiento (Soporta múltiples usuarios)
serve(app, host='0.0.0.0', port=5000, threads=6)