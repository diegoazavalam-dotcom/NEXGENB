import time
import threading
import logging

# Importaciones de tu proyecto
import database
from plc_driver import SiemensDriver

# Manejo robusto de alertas (si el archivo no existe, no rompe el sistema)
try:
    import alerts
except ImportError:
    alerts = None

class SensorGateway:
    def __init__(self, modo_produccion=False):
        self.running = False
        # Diccionario para trackear el estado y EVITAR SPAM DE ALERTAS
        self.sensores_en_alerta = {} 
        self.sensores_config = [] 
        
        self.modo_produccion = modo_produccion
        
        # Instanciamos el driver.
        self.driver = SiemensDriver(ip="192.168.0.20", simulation=not modo_produccion)
        print(f"✅ [GATEWAY] Driver inicializado (Modo Producción: {modo_produccion})")

    def cargar_configuracion(self, lista_sensores_db):
        """Recibe la lista de la Base de Datos y la prepara para el PLC"""
        self.sensores_config = [dict(s) for s in lista_sensores_db]
        
        # Inicializamos el estado de todos los sensores como "OK"
        for s in self.sensores_config:
            if s.get('n') not in self.sensores_en_alerta:
                self.sensores_en_alerta[s.get('n')] = "OK"

    def start(self):
        """Arranca el hilo de telemetría sin bloquear el programa principal"""
        if not self.running:
            self.running = True
            hilo = threading.Thread(target=self._ciclo_telemetria, daemon=True)
            hilo.start()
            print("🚀 [GATEWAY] Motor de Telemetría Activo")

    def get_connection_status(self):
        """Método público para que la APP pregunte si el PLC está vivo"""
        try:
            return self.driver.connected
        except AttributeError:
            return False

    def _ciclo_telemetria(self):
        """Ciclo principal de captura de datos optimizado para S7-1200"""
        ultimo_mantenimiento = time.time()
        while self.running:
            try:
                # 0. Mantenimiento programado (cada 24 horas = 86400 segundos)
                if time.time() - ultimo_mantenimiento > 86400:
                    print("🧹 [GATEWAY] Ejecutando poda y mantenimiento de la base de datos...")
                    database.ejecutar_mantenimiento_db(7, 90) # 7 días tabla principal, 90 días archivo
                    ultimo_mantenimiento = time.time()

                # 1. Validar si hay sensores configurados
                if not self.sensores_config:
                    time.sleep(1)
                    continue

                datos_para_guardar = [] # Lista temporal para el batch insert

                # 2. Asegurar conexión antes de empezar el barrido
                # Si el driver está desconectado, intentamos conectar UNA VEZ por ciclo.
                if not self.driver.get_connected_status():
                    print("🔄 [GATEWAY] Intentando reconectar al PLC...")
                    if not self.driver.conectar():
                        # Si falla la conexión, esperamos 5 segundos antes de reintentar
                        # para no hacer "spam" de intentos de conexión fallidos.
                        print("⚠️ [GATEWAY] Reconexión fallida. Esperando 5s...")
                        time.sleep(5)
                        continue # Saltamos el resto del ciclo (no leemos sensores)

                # 3. Barrido de Sensores (Solo llegamos aquí si hay conexión o estamos en simulación)
                for s in self.sensores_config:
                    try:
                        # --- EXTRACCIÓN SINCRONIZADA CON DATABASE.PY ---
                        n = s.get('nombre_sensor') 
                        
                        # Si por alguna razón el nombre viene vacío, saltamos para evitar el crash en PostgreSQL
                        if not n:
                            continue 
                            
                        db_n = int(s.get('db_number', 1))
                        off = float(s.get('offset_val', 0.0))
                        tipo = s.get('tipo_metrica', 'REAL')
                        unidad = s.get('unidad', '')
                        
                        limite_alto = float(s.get('limite_alto', 100.0))
                        limite_bajo = float(s.get('limite_bajo', 0.0))

                        # Leemos el valor del PLC
                        valor_actual = self.driver.leer_sensor(
                            db_number=db_n, 
                            offset=off, 
                            tipo=tipo
                        )
                        
                        # Manejo seguro: Si la lectura devuelve None (falla), forzamos un valor seguro o saltamos
                        if valor_actual is None:
                            print(f"⚠️ [GATEWAY] Lectura nula en {n}. Saltando...")
                            continue # Pasamos al siguiente sensor
                            
                        # Acumulamos para el guardado histórico masivo
                        datos_para_guardar.append((n, valor_actual))
                        
                        # --- LÓGICA DE ALERTAS ANTI-SPAM (FLANCO DE SUBIDA) ---
                        estado_previo = self.sensores_en_alerta.get(n, "OK")
                        estado_actual = "OK"

                        # Evaluamos el valor actual
                        if valor_actual >= limite_alto:
                            estado_actual = "ALTO"
                        elif valor_actual <= limite_bajo:
                            estado_actual = "BAJO"

                        # SOLO REGISTRAMOS SI ACABA DE SALIRSE DE CONTROL (Cambio de estado)
                        if estado_actual != "OK" and estado_previo == "OK":
                            
                            umbral_roto = limite_alto if estado_actual == "ALTO" else limite_bajo
                            database.registrar_incidencia_db(n, valor_actual, umbral_roto, estado_actual)
                            
                            if alerts:
                                alerts.procesar_alerta_banda(n, valor_actual, limite_bajo, limite_alto, unidad)
                            
                            # Bloqueamos el sensor para no enviar más spam
                            self.sensores_en_alerta[n] = estado_actual
                            print(f"🚨 [ALERTA] Sensor {n} superó el umbral ({estado_actual}). Candado activado.")
                            
                        # SI EL SENSOR VOLVIÓ A LA NORMALIDAD, QUITAMOS EL CANDADO
                        elif estado_actual == "OK" and estado_previo != "OK":
                            self.sensores_en_alerta[n] = "OK"
                            print(f"✅ [RESTAURADO] Sensor {n} volvió a la normalidad. Candado liberado.")

                    except Exception as e_sensor:
                        print(f"❌ Error leyendo sensor {s.get('n', 'Desconocido')}: {e_sensor}")
                        continue

                # 4. Guardado en Bloque: Una sola escritura en disco por segundo
                if datos_para_guardar:
                    database.guardar_bloque_telemetria(datos_para_guardar)

            except Exception as e:
                print(f"🔥 Error Crítico Gateway: {e}")
                time.sleep(5) 
            
            # 5. Frecuencia de muestreo estricta (1 Hz)
            time.sleep(1)