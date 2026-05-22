import random
from abc import ABC, abstractmethod

# Intentar importar snap7 para producción
try:
    import snap7
    from snap7.util import get_real, get_int, get_bool, set_real, set_int, set_bool
    SNAP7_INSTALLED = True
except ImportError:
    SNAP7_INSTALLED = False
    print("⚠️ [PLC] Librería snap7 no encontrada. Solo modo simulación disponible.")

# Intentar importar pymodbus para producción
try:
    from pymodbus.client import ModbusTcpClient
    from pymodbus.payload import BinaryPayloadDecoder
    from pymodbus.payload import BinaryPayloadBuilder
    from pymodbus.constants import Endian
    PYMODBUS_INSTALLED = True
except ImportError:
    PYMODBUS_INSTALLED = False
    print("⚠️ [PLC] Librería pymodbus no encontrada. Solo modo simulación Modbus disponible.")

# Intentar importar pysnmp para el motor SNMP encubierto
try:
    from pysnmp.hlapi import getCmd, SnmpEngine, CommunityData, UdpTransportTarget, ContextData, ObjectType, ObjectIdentity
    PYSNMP_INSTALLED = True
except ImportError:
    PYSNMP_INSTALLED = False
    print("⚠️ [PLC] Librería pysnmp no encontrada. Solo simulación SNMP disponible.")

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

    @abstractmethod
    def escribir_sensor(self, db_number, offset, tipo, valor): pass

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

    def escribir_sensor(self, db_number, offset, tipo, valor):
        if self.simulation:
            print(f"🛠️ [SIMULACION] Escribiendo {valor} en DB{db_number}.DBX{offset} ({tipo})")
            return True
            
        if not self.get_connected_status():
            if not self.conectar():
                return False
                
        try:
            byte_index = int(float(offset))
            bit_index = int(round((float(offset) - byte_index) * 10))

            if tipo == 'BOOL':
                # Para booleanos leemos el byte, cambiamos el bit y sobreescribimos
                data = self.client.db_read(int(db_number), byte_index, 1)
                set_bool(data, 0, bit_index, bool(int(valor)))
                self.client.db_write(int(db_number), byte_index, data)
                return True
                
            elif tipo == 'INT':
                data = bytearray(2)
                set_int(data, 0, int(valor))
                self.client.db_write(int(db_number), byte_index, data)
                return True
                
            elif tipo == 'REAL':
                data = bytearray(4)
                set_real(data, 0, float(valor))
                self.client.db_write(int(db_number), byte_index, data)
                return True
                
            return False
        except Exception as e:
            print(f"❌ Error escribiendo DB{db_number}.DBX{offset}: {e}")
            return False

# =========================================================
# DRIVER MOCK PARA AUDITORÍA
# =========================================================
class MockDriver(BaseGateway):
    """Driver que no requiere red ni snap7, ideal para pruebas unitarias CI/CD"""
    def conectar(self): return True
    def get_connected_status(self): return True
    def leer_sensor(self, db_number, offset, tipo, limite_referencia=100):
        return round(random.uniform(20, 30), 2)
    def escribir_sensor(self, db_number, offset, tipo, valor):
        return True

# =========================================================
# DRIVER MODBUS TCP
# =========================================================
class ModbusDriver(BaseGateway):
    def __init__(self, ip, port=502, simulation=True):
        self.ip = ip
        self.port = port
        self.simulation = simulation or not PYMODBUS_INSTALLED
        self.client = None
        self.connected = False

    def get_connected_status(self):
        if self.simulation: 
            return True
        try:
            return self.client.connect() if self.client else False
        except: 
            return False

    def conectar(self):
        if self.simulation: 
            self.connected = True
            return True
            
        try:
            print(f"🔄 Intentando conectar a Modbus TCP en {self.ip}:{self.port}...")
            if self.client is None:
                self.client = ModbusTcpClient(self.ip, port=self.port, timeout=3)
                
            self.connected = self.client.connect()
            return self.connected
        except Exception as e: 
            print(f"❌ Error de conexión Modbus: {e}")
            self.connected = False
            return False

    def desconectar(self):
        if self.simulation:
            self.connected = False
            return
        try:
            if self.client:
                self.client.close()
                print(f"🔌 Socket Modbus desconectado limpiamente de {self.ip}")
        except:
            pass
        finally:
            self.connected = False

    def actualizar_conexion(self, nueva_ip):
        nueva_ip = str(nueva_ip).strip() 
        if self.ip != nueva_ip:
            print(f"🔄 Cambio de IP Modbus detectado: {self.ip} -> {nueva_ip}")
            self.desconectar()
            self.ip = nueva_ip
            self.client = None
            return self.conectar()
        return True

    def leer_sensor(self, db_number, offset, tipo, limite_referencia=100):
        if self.simulation:
            base = float(limite_referencia) if limite_referencia else 50.0
            ruido = random.uniform(-2.0, 2.0)
            if tipo == 'BOOL': return random.choice([0, 1])
            if tipo == 'INT': return int(base + ruido)
            return round(base + ruido, 2)
            
        if not self.get_connected_status():
            if not self.conectar():
                return 0.0
            
        try:
            address = int(float(offset))
            count = 2 if tipo == 'REAL' else 1
            
            # Asumimos Holding Registers (función 3)
            response = self.client.read_holding_registers(address=address, count=count, slave=1)
            
            if response.isError():
                print(f"⚠️ Error Modbus leyendo registro {address}")
                return 0.0

            if tipo == 'BOOL':
                return 1 if response.registers[0] > 0 else 0
            elif tipo == 'INT':
                decoder = BinaryPayloadDecoder.fromRegisters(response.registers, byteorder=Endian.Big, wordorder=Endian.Big)
                return decoder.decode_16bit_int()
            elif tipo == 'REAL':
                decoder = BinaryPayloadDecoder.fromRegisters(response.registers, byteorder=Endian.Big, wordorder=Endian.Little)
                return round(decoder.decode_32bit_float(), 2)
            
            return 0.0
        except Exception as e: 
            print(f"⚠️ Error leyendo Modbus TCP en {address}: {e}")
            self.connected = False 
            return 0.0

    def escribir_sensor(self, db_number, offset, tipo, valor):
        if self.simulation:
            print(f"🛠️ [SIMULACION MODBUS] Escribiendo {valor} en HR {offset} ({tipo})")
            return True
            
        if not self.get_connected_status():
            if not self.conectar():
                return False
                
        try:
            address = int(float(offset))
            if tipo == 'BOOL':
                val = 1 if int(valor) > 0 else 0
                self.client.write_register(address=address, value=val, slave=1)
                return True
            elif tipo == 'INT':
                self.client.write_register(address=address, value=int(valor), slave=1)
                return True
            elif tipo == 'REAL':
                builder = BinaryPayloadBuilder(byteorder=Endian.Big, wordorder=Endian.Little)
                builder.add_32bit_float(float(valor))
                payload = builder.to_registers()
                self.client.write_registers(address=address, values=payload, slave=1)
                return True
            return False
        except Exception as e:
            print(f"❌ Error escribiendo Modbus TCP en HR {offset}: {e}")
            return False

# =========================================================
# DRIVER SNMP (AGENTE ENCUBIERTO HARDWARE)
# =========================================================
class SNMPDriver(BaseGateway):
    def __init__(self, ip, port=161, community='public', simulation=True):
        self.ip = ip
        self.port = port
        self.community = community
        self.simulation = simulation or not PYSNMP_INSTALLED
        self.connected = False

    def get_connected_status(self):
        return True # UDP connectionless

    def conectar(self):
        self.connected = True
        return True

    def leer_sensor(self, db_number, offset, tipo, limite_referencia=100):
        if self.simulation:
            ruido = random.uniform(-2.0, 2.0)
            if offset == 1.0: return round(30.0 + ruido, 2) # Sim CPU
            elif offset == 2.0: return round(45.0 + ruido, 2) # Sim RAM
            elif offset == 3.0: return round(60.0 + ruido, 2) # Sim Disk
            return random.choice([0, 1]) if tipo == 'BOOL' else round(50.0 + ruido, 2)

        try:
            # Mapeo de Offset a OIDs del Agente Encubierto
            # offset 1.0 -> CPU OID: 1.3.6.1.4.1.9999.1.1.0
            # offset 2.0 -> RAM OID: 1.3.6.1.4.1.9999.1.2.0
            # offset 3.0 -> DISK OID: 1.3.6.1.4.1.9999.1.3.0
            idx = int(float(offset))
            oid_str = f'1.3.6.1.4.1.9999.1.{idx}.0'

            errorIndication, errorStatus, errorIndex, varBinds = next(
                getCmd(SnmpEngine(),
                       CommunityData(self.community, mpModel=0),
                       UdpTransportTarget((self.ip, self.port), timeout=2.0, retries=1),
                       ContextData(),
                       ObjectType(ObjectIdentity(oid_str)))
            )

            if errorIndication or errorStatus:
                return 0.0

            for name, val in varBinds:
                # El valor retornado por el agente SNMP en string lo pasamos a float
                return round(float(val.prettyPrint()), 2)

            return 0.0
        except Exception as e:
            print(f"⚠️ Error leyendo SNMP en {self.ip} (OID Index {offset}): {e}")
            return 0.0

    def escribir_sensor(self, db_number, offset, tipo, valor):
        # SNMP Get-Only para hardware monitoring
        return False