import random
from abc import ABC, abstractmethod

# Intentar importar snap7 para producción
try:
    import snap7
    from snap7.util import get_real, get_int, get_bool
    SNAP7_INSTALLED = True
except ImportError:
    SNAP7_INSTALLED = False
    print("⚠️ [PLC] Librería snap7 no encontrada. Solo modo simulación disponible.")

# =========================================================
# CONTRATO UNIVERSAL (Interface)
# =========================================================
class BaseGateway(ABC):
    @abstractmethod
    def conectar(self): pass
    
    @abstractmethod
    def get_connected_status(self): pass
    
    @abstractmethod
    def leer_sensor(self, db_number, offset, tipo, limite_referencia=100): pass

# =========================================================
# DRIVER SIEMENS S7 (Implementación real)
# =========================================================
class SiemensDriver(BaseGateway):
    def __init__(self, ip, rack=0, slot=1, simulation=True):
        self.ip = ip
        self.rack = rack
        self.slot = slot
        # Si no hay librería snap7, forzamos simulación por seguridad
        self.simulation = simulation or not SNAP7_INSTALLED
        self.client = None
        self.connected = False

    def get_connected_status(self):
        if self.simulation: 
            return True
        try:
            return self.client.get_connected() if self.client else False
        except: 
            return False

    def conectar(self):
        if self.simulation: 
            self.connected = True
            return True
            
        try:
            print(f"🔄 Intentando conectar al PLC Siemens en {self.ip} (Rack {self.rack}, Slot {self.slot})...")
            
            # 🔥 PARCHE EXE: Solo creamos el cliente si no existe. 
            # Si ya existe (Hot Reload), reutilizamos el mismo objeto en memoria.
            if self.client is None:
                self.client = snap7.client.Client()
                
            self.client.connect(self.ip, self.rack, self.slot)
            self.connected = self.client.get_connected()
            return self.connected
        except Exception as e: 
            print(f"❌ Error de conexión Siemens: {e}")
            self.connected = False
            return False

    def desconectar(self):
        """Cierra el socket TCP actual de forma limpia pero MANTIENE el objeto para el .exe"""
        if self.simulation:
            self.connected = False
            return
            
        try:
            if self.client and self.get_connected_status():
                self.client.disconnect()
                print(f"🔌 Socket desconectado limpiamente de {self.ip}")
                # 🚫 ELIMINAMOS self.client.destroy() y self.client = None
                # Esto evita que la DLL colapse dentro de PyInstaller
        except Exception as e:
            pass # Ignoramos errores si ya estaba desconectado
        finally:
            self.connected = False

    def actualizar_conexion(self, nueva_ip):
        """Mata la conexión vieja y levanta una nueva (Hot Reload Seguro)"""
        nueva_ip = str(nueva_ip).strip() 
        
        if self.ip != nueva_ip:
            print(f"🔄 Cambio de IP detectado: {self.ip} -> {nueva_ip}")
            self.desconectar()
            self.ip = nueva_ip
            return self.conectar()
        return True # Si es la misma IP, no hacemos nada

    def leer_sensor(self, db_number, offset, tipo, limite_referencia=100):
        # 1. SI ESTAMOS EN SIMULACIÓN, INVENTAMOS EL DATO
        if self.simulation:
            base = float(limite_referencia) if limite_referencia else 50.0
            ruido = random.uniform(-10.0, 10.0)
            if tipo == 'BOOL': return random.choice([0, 1])
            if tipo == 'INT': return int((base * 0.5) + ruido)
            return round((base * 0.5) + ruido, 2)
            
        # 2. SI ESTAMOS EN PRODUCCIÓN, EXIGIMOS CONEXIÓN REAL
        if not self.get_connected_status():
            if not self.conectar():
                return 0.0 # Valor seguro en caso de desconexión para no romper el SCADA
            
        # 3. LECTURA FÍSICA
        try:
            # Separar el offset en Byte y Bit (ej. 0.5 -> Byte 0, Bit 5)
            byte_index = int(float(offset))
            bit_index = int(round((float(offset) - byte_index) * 10))

            size = 4
            if tipo == 'INT': size = 2
            elif tipo == 'BOOL': size = 1
            
            data = self.client.db_read(int(db_number), byte_index, size)
            
            if tipo == 'REAL': return round(get_real(data, 0), 2)
            elif tipo == 'INT': return get_int(data, 0)
            elif tipo == 'BOOL': return 1 if get_bool(data, 0, bit_index) else 0
            
            return 0.0
        except Exception as e: 
            print(f"⚠️ Error leyendo DB{db_number}.DBX{offset}: {e}")
            self.connected = False 
            return 0.0

# =========================================================
# DRIVER MOCK PARA AUDITORÍA
# =========================================================
class MockDriver(BaseGateway):
    """Driver que no requiere red ni snap7, ideal para pruebas unitarias CI/CD"""
    def conectar(self): return True
    def get_connected_status(self): return True
    def leer_sensor(self, db_number, offset, tipo, limite_referencia=100):
        return round(random.uniform(20, 30), 2)