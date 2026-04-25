import time
import asyncio
import logging
from asyncua import Client
import database
from plc_driver import SiemensDriver  # Tu driver actual

# Configuración de Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [GATEWAY] - %(message)s')

class UniversalGateway:
    def __init__(self):
        self.running = True
        # Cache de conexiones Siemens para no reconectar en cada ciclo
        self.drivers_s7 = {} 

    async def leer_opcua(self, sensor):
        """Lee un nodo específico de un servidor OPC UA"""
        url = f"opc.tcp://{sensor['ip_plc']}:4840" # Puerto estándar OPC UA
        nodo_id = sensor['nodo_id']
        
        try:
            async with Client(url=url) as client:
                # En producción, mantendríamos la conexión abierta, 
                # aquí conectamos y desconectamos por simplicidad y robustez
                node = client.get_node(nodo_id)
                valor = await node.read_value()
                return float(valor)
        except Exception as e:
            logging.error(f"Fallo OPC-UA {sensor['n']}: {e}")
            return None

    def leer_siemens(self, sensor):
        """Usa tu lógica existente de Snap7"""
        ip = sensor['id_conexion'] # En S7 usamos id_conexion como IP
        
        # Gestión de conexión persistente
        if ip not in self.drivers_s7:
            # Asumimos Rack 0 Slot 1 por defecto, o podrías guardarlo en DB
            self.drivers_s7[ip] = SiemensDriver(ip, 0, 1, simulation=True) # PONER FALSE PARA REAL
        
        driver = self.drivers_s7[ip]
        
        # Mapeo de tipos
        tipo = sensor['tipo_metrica'] # REAL, INT, etc
        db = sensor['db_number']
        off = sensor['offset_val'] # Ojo: en Postgres lo llamamos offset_val
        
        try:
            val = driver.leer_sensor(db, off, tipo)
            return val
        except Exception as e:
            logging.error(f"Fallo Siemens {sensor['n']}: {e}")
            return None

    async def ciclo_principal(self):
        logging.info("🚀 INICIANDO GATEWAY UNIVERSAL (S7 + OPC-UA)")
        
        while self.running:
            inicio = time.time()
            
            # 1. Obtener sensores activos de la DB
            sensores = database.leer_configuracion_sensores()
            datos_para_guardar = []
            
            # 2. Procesar lecturas
            for s in sensores:
                valor = None
                protocolo = s.get('protocolo', 'S7') # Por defecto S7 si es null
                
                if protocolo == 'OPCUA':
                    # Lectura Asíncrona
                    valor = await self.leer_opcua(s)
                    
                elif protocolo == 'S7':
                    # Lectura Síncrona (Tu driver actual)
                    valor = self.leer_siemens(s)
                
                # 3. Preparar paquete de datos
                if valor is not None:
                    datos_para_guardar.append((s['nombre_sensor'], valor))
                    
                    # Verificación de Alertas (Telegram)
                    umbral = s.get('limite_alerta', 100.0)
                    if valor >= umbral:
                        # Aquí podrías llamar a tu lógica de Telegram
                        # database.registrar_incidencia_db(...)
                        pass

            # 4. Guardado Masivo en PostgreSQL (Alta eficiencia)
            if datos_para_guardar:
                database.guardar_bloque_telemetria(datos_para_guardar)
                logging.info(f"💾 Guardados {len(datos_para_guardar)} registros.")
            
            # 5. Control de frecuencia (Polling cada 2 segundos)
            tiempo_proceso = time.time() - inicio
            sleep_time = max(0, 2.0 - tiempo_proceso)
            await asyncio.sleep(sleep_time)

if __name__ == "__main__":
    gateway = UniversalGateway()
    try:
        # Ejecutar el loop asíncrono
        asyncio.run(gateway.ciclo_principal())
    except KeyboardInterrupt:
        print("🛑 Gateway detenido manualmente.")