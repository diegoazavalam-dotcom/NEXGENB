import os
import sys
import json

# --- MAGIA DE RUTAS PARA PYINSTALLER ---
if getattr(sys, 'frozen', False):
    # Si estamos corriendo como .exe, la carpeta base es donde está el .exe
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # Si estamos corriendo en crudo (python app.py)
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# El archivo siempre vivirá al lado del ejecutable
CONFIG_FILE = os.path.join(BASE_DIR, 'config_maestra.json')

def leer_config_maestra():
    """Lee el archivo JSON. Si no existe, lo crea automáticamente."""
    if not os.path.exists(CONFIG_FILE):
        print("⚠️ Archivo de configuración maestro no encontrado. Creando valores por defecto...")
        config_default = {
            "plc": {
                "ip": "192.168.0.20", 
                "rack": 0, 
                "slot": 1, 
                "simulacion": True
            },
            "database": {
                "retencion_principal_dias": 7, 
                "retencion_archivo_dias": 90
            },
            "sistema": {
                "polling_ms": 1000, 
                "log_level": "INFO"
            },
            "licencia": {
                "cliente": "Planta", 
                "expiracion": "2026-12-31", 
                "mac_autorizada": "ANY"
            }
        }
        guardar_config_maestra(config_default)
        return config_default

    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error leyendo config JSON: {e}")
        return {}

def guardar_config_maestra(data):
    """Escribe los cambios del GodMode en el JSON."""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        return True
    except Exception as e:
        print(f"❌ Error guardando config maestra: {e}")
        return False