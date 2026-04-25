import json
import os
import subprocess
from cryptography.fernet import Fernet
from datetime import datetime

LLAVE_MAESTRA = b'lQv8_7mHk_Z3nQjB4xL_T9gP2wV5rF8yD1sC6mN4xQo='

def obtener_hardware_id():
    """Obtiene el UUID de la placa base en Windows."""
    try:
        output = subprocess.check_output("wmic csproduct get uuid", shell=True).decode()
        uuid = output.split('\n')[1].strip()
        if not uuid or uuid == 'FFFFFFFF-FFFF-FFFF-FFFF-FFFFFFFFFFFF':
            # Fallback a MachineGuid
            import winreg
            registry = winreg.HKEY_LOCAL_MACHINE
            address = r"SOFTWARE\Microsoft\Cryptography"
            key = winreg.OpenKey(registry, address, 0, winreg.KEY_READ)
            uuid, _ = winreg.QueryValueEx(key, "MachineGuid")
            winreg.CloseKey(key)
        return uuid
    except Exception as e:
        print(f"Error obteniendo HWID: {e}")
        return "UNKNOWN_HWID"

def generar_licencia():
    print("=== GENERADOR DE LICENCIAS ZOLe ===")
    
    cliente = input("Nombre del Cliente: ")
    expiracion = input("Fecha de expiración (YYYY-MM-DD): ")
    
    print("\nNiveles de Licencia:")
    print("1. BÁSICO (Max 10 Nodos)")
    print("2. PRO (Max 50 Nodos)")
    print("3. EMPRESARIAL (Ilimitado)")
    print("4. CUSTOM (Límite manual para integradores)")
    
    op = input("Selecciona el nivel (1-4): ")
    
    nivel = "BASICO"
    max_nodos = 10
    
    if op == '2':
        nivel = "PRO"
        max_nodos = 50
    elif op == '3':
        nivel = "EMPRESARIAL"
        max_nodos = 9999
    elif op == '4':
        nivel = "CUSTOM"
        max_nodos = int(input("Ingresa la cantidad máxima de nodos permitida: "))
    
    print("\n¿Deseas amarrar esta licencia al hardware actual (Servidor local)?")
    amarre = input("(s/n): ").lower()
    
    hwid = "ANY"
    if amarre == 's':
        hwid = obtener_hardware_id()
        print(f"Hardware ID detectado: {hwid}")
    elif amarre == 'n':
        hwid_manual = input("Ingresa el Hardware ID del servidor del cliente (O presiona Enter para omitir candado): ")
        if hwid_manual.strip():
            hwid = hwid_manual.strip()

    payload = {
        "cliente": cliente,
        "expiracion": expiracion,
        "nivel": nivel,
        "max_nodos": max_nodos,
        "hwid": hwid,
        "generada": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    payload_str = json.dumps(payload)
    f = Fernet(LLAVE_MAESTRA)
    token = f.encrypt(payload_str.encode('utf-8'))
    
    with open("license.key", "wb") as file:
        file.write(token)
        
    print("\n✅ ¡Licencia generada con éxito en 'license.key'!")
    print(f"Resumen: {payload}")

if __name__ == '__main__':
    generar_licencia()
