import os
import json
import subprocess
from datetime import datetime
from cryptography.fernet import Fernet

LLAVE_MAESTRA = b'lQv8_7mHk_Z3nQjB4xL_T9gP2wV5rF8yD1sC6mN4xQo='
import sys
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    
LICENSE_FILE = os.path.join(BASE_DIR, 'license.key')
SYS_TIME_FILE = os.path.join(BASE_DIR, '.sys_time')

def obtener_hardware_id():
    """Obtiene el UUID de la máquina (Soporta Windows y Linux/Docker)."""
    try:
        if os.name == 'nt':
            output = subprocess.check_output("wmic csproduct get uuid", shell=True, stderr=subprocess.DEVNULL).decode()
            uuid = output.split('\n')[1].strip()
            if not uuid or uuid == 'FFFFFFFF-FFFF-FFFF-FFFF-FFFFFFFFFFFF':
                import winreg
                registry = winreg.HKEY_LOCAL_MACHINE
                address = r"SOFTWARE\Microsoft\Cryptography"
                key = winreg.OpenKey(registry, address, 0, winreg.KEY_READ)
                uuid, _ = winreg.QueryValueEx(key, "MachineGuid")
                winreg.CloseKey(key)
            return uuid
        else:
            if os.path.exists('/etc/machine-id'):
                with open('/etc/machine-id', 'r') as f: return f.read().strip()
            elif os.path.exists('/var/lib/dbus/machine-id'):
                with open('/var/lib/dbus/machine-id', 'r') as f: return f.read().strip()
            return "UNKNOWN_HWID"
    except Exception:
        return "UNKNOWN_HWID"

def verificar_tampering_reloj(hoy_str):
    """Guarda y compara la fecha actual para evitar que el usuario atrase el reloj."""
    try:
        f = Fernet(LLAVE_MAESTRA)
        if os.path.exists(SYS_TIME_FILE):
            with open(SYS_TIME_FILE, 'r') as file:
                encriptado = file.read().strip()
                ultima_fecha_str = f.decrypt(encriptado.encode('utf-8')).decode('utf-8')
                
                # Si la fecha de hoy es MENOR que la última fecha registrada, hubo tampering
                if hoy_str < ultima_fecha_str:
                    return False
        
        # DEFENSA ADICIONAL: Si borran .sys_time, comparamos contra la fecha del código fuente principal
        # Si el usuario atrasa el reloj más allá de la fecha en la que se instaló el sistema, se bloquea.
        app_file = os.path.join(BASE_DIR, 'app.py')
        if os.path.exists(app_file):
            mtime = os.path.getmtime(app_file)
            mtime_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
            if hoy_str < mtime_str:
                print("🚫 [LICENCIA] Tampering detectado: El reloj es anterior a la fecha de instalación.")
                return False
                    
        # Actualizamos la fecha máxima registrada
        with open(SYS_TIME_FILE, 'w') as file:
            nuevo_encriptado = f.encrypt(hoy_str.encode('utf-8')).decode('utf-8')
            file.write(nuevo_encriptado)
        return True
    except Exception:
        # En caso de error (archivo corrupto por el usuario), asumimos tampering por seguridad
        return False

def verificar_licencia():
    print(f"🔍 [LICENCIA] Buscando archivo en: {LICENSE_FILE}")
    
    if not os.path.exists(LICENSE_FILE):
        return {"valida": False, "error": "No se encontró el archivo de licencia (license.key)."}
        
    try:
        with open(LICENSE_FILE, 'r') as file:
            token = file.read().strip()
            
        f = Fernet(LLAVE_MAESTRA)
        payload = f.decrypt(token.encode('utf-8')).decode('utf-8')
        datos = json.loads(payload)
        
        # 1. VERIFICACIÓN DE EXPIRACIÓN
        fecha_exp = datetime.strptime(datos['expiracion'], "%Y-%m-%d")
        hoy = datetime.now()
        hoy_str = hoy.strftime("%Y-%m-%d %H:%M:%S")
        dias_restantes = (fecha_exp - hoy).days
        
        if dias_restantes < 0:
            return {"valida": False, "error": f"La licencia expiró el {datos['expiracion']}."}
            
        # 2. ANTI-TIME TAMPERING
        if not verificar_tampering_reloj(hoy_str):
            return {"valida": False, "error": "SEGURIDAD: Se detectó alteración en el reloj del sistema operativo."}
            
        # 3. VERIFICACIÓN DE HARDWARE (HWID LOCK)
        hwid_licencia = datos.get('hwid', 'ANY')
        if hwid_licencia != 'ANY':
            hwid_actual = obtener_hardware_id()
            if hwid_licencia != hwid_actual:
                return {"valida": False, "error": f"SEGURIDAD: La licencia no pertenece a este servidor (HWID Mismatch)."}
        
        # 4. EXTRACCIÓN DE NIVELES Y NODOS
        nivel = datos.get('nivel', 'BASICO')
        max_nodos = datos.get('max_nodos', 10)
            
        return {
            "valida": True, 
            "cliente": datos.get('cliente', 'Desconocido'), 
            "dias_restantes": dias_restantes,
            "nivel": nivel,
            "max_nodos": max_nodos
        }
        
    except Exception as e:
        print(f"❌ [LICENCIA] Error al leer/desencriptar: {e}")
        return {"valida": False, "error": "Licencia corrupta o inválida."}