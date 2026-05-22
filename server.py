from app import app, socketio
import socket
import eventlet

# Necesario para que eventlet intercepte operaciones síncronas (como time.sleep)
eventlet.monkey_patch()

# Obtener la IP real de la máquina para mostrarla en consola
hostname = socket.gethostname()
local_ip = socket.gethostbyname(hostname)

print("---------------------------------------------------------")
print(f"🏭 SCADA NEXGEN SERVER - MODO WEBSOCKETS (Eventlet)")
print(f"📡 Escuchando en: http://{local_ip}:5000")
print("---------------------------------------------------------")

# Lanzamos el servidor asíncrono con SocketIO
socketio.run(app, host='0.0.0.0', port=5000)