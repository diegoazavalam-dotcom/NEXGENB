import requests
import time
import threading
import database

# --- CONFIGURACIÓN Y ESTADO ---
historial_alertas = {}  
# Usamos un solo diccionario para el caché
_config_cache = {"token": None, "chat_id": None, "activo": 0, "last_update": 0}

def recargar_config():
    """
    Fuerza la recarga del caché. Es llamada desde app.py cuando el 
    usuario guarda nuevas credenciales de Telegram en el SCADA.
    """
    global _config_cache
    _config_cache["last_update"] = 0 # Forzamos a que obtener_config_rapida consulte la DB

def obtener_config_rapida(bot_type='operativo'):
    global _config_cache 
    ahora = time.time()
    
    if bot_type not in _config_cache:
        _config_cache[bot_type] = {"token": None, "chat_id": None, "activo": 0, "last_update": 0}

    # Si han pasado más de 30 segundos, refrescamos desde la DB (PostgreSQL)
    if (ahora - _config_cache[bot_type]["last_update"]) > 30 or not _config_cache[bot_type].get("token"):
        try:
            conf = database.config_telegram('get', bot_type=bot_type)
            if conf:
                _config_cache[bot_type]["token"] = conf.get('token')
                _config_cache[bot_type]["chat_id"] = conf.get('chat_id')
                _config_cache[bot_type]["activo"] = conf.get('activo', 0)
                _config_cache[bot_type]["last_update"] = ahora
        except Exception as e:
            print(f"❌ [ALERTS] Error refrescando caché: {e}")
            
    return _config_cache[bot_type]

def _enviar_telegram_async(msg, bot_type='operativo'):
    """Envía el mensaje en un hilo separado para no bloquear el PLC"""
    conf = obtener_config_rapida(bot_type)
    
    token = conf.get("token")
    chat_id = conf.get("chat_id")
    activo = conf.get("activo")

    # Si no está activo o faltan datos, abortamos silenciosamente
    if not activo or not token or not chat_id:
        return 

    def task(t_token, t_chat_id, texto):
        try:
            url = f"https://api.telegram.org/bot{t_token}/sendMessage"
            # Aumentamos el timeout para redes industriales lentas
            respuesta = requests.post(url, data={
                "chat_id": t_chat_id, 
                "text": texto, 
                # CAMBIO 1: Usamos HTML para evitar el conflicto con los guiones bajos de los nombres
                "parse_mode": "HTML" 
            }, timeout=10)
            
            # Verificamos si Telegram rechazó el mensaje (ej: token inválido)
            if respuesta.status_code != 200:
                print(f"⚠️ [TELEGRAM] Error de API: {respuesta.text}")
                
        except Exception as e:
            print(f"⚠️ [TELEGRAM] Falla de red: {e}")

    # Lanzamos el hilo demonio
    threading.Thread(target=task, args=(token, chat_id, msg), daemon=True).start()

# --- FUNCIÓN MAESTRA (Sincronizada con el Ciclo del Gateway) ---

def procesar_alerta_banda(nombre, valor, l_bajo, l_alto, unidad):
    """
    Gestiona las notificaciones de Telegram para límites duales.
    Llamada desde sensor_gateway.py.
    """
    global historial_alertas
    ahora = time.time()
    
    try:
        v = float(valor)
        lb = float(l_bajo)
        la = float(l_alto)
    except ValueError:
        return # Si los datos vienen corruptos del PLC, no hacemos nada

    es_falla_baja = v <= lb
    es_falla_alta = v >= la
    esta_en_rango = not (es_falla_baja or es_falla_alta)

    # 1. LÓGICA DE ALERTA (Anti-Spam 60s)
    if not esta_en_rango:
        ultimo_aviso = historial_alertas.get(nombre, 0)
        
        # Si pasaron 60 segundos desde el último aviso para este sensor
        if (ahora - ultimo_aviso) > 60:
            icono = "🔴" if es_falla_baja else "⚠️"
            tipo = "LÍMITE INFERIOR" if es_falla_baja else "LÍMITE SUPERIOR"
            umbral = lb if es_falla_baja else la

            # CAMBIO 2: Usamos <b> en lugar de * para el formato HTML
            msg = (f"{icono} <b>ALERTA DE SEGURIDAD</b>\n"
                   f"Sensor: {nombre}\n"
                   f"Estado: {tipo} VIOLADO\n"
                   f"Valor: {v} {unidad}\n"
                   f"Umbral: {umbral} {unidad}")
            
            # Si el nombre empieza con Linux_, enviamos al canal de TI
            bot_t = 'ti' if nombre.startswith('Linux_') else 'operativo'
            _enviar_telegram_async(msg, bot_type=bot_t)
            # Actualizamos la marca de tiempo
            historial_alertas[nombre] = ahora

    # 2. LÓGICA DE RECUPERACIÓN (Aviso de normalización)
    elif esta_en_rango and (nombre in historial_alertas):
        # CAMBIO 3: Usamos <b> en lugar de * para el formato HTML
        msg = (f"✅ <b>SISTEMA NORMALIZADO</b>\n"
               f"Sensor: {nombre}\n"
               f"El valor {v} {unidad} ha regresado al rango operativo seguro.")
        
        bot_t = 'ti' if nombre.startswith('Linux_') else 'operativo'
        _enviar_telegram_async(msg, bot_type=bot_t)
        # Limpiamos el historial para que pueda volver a alertar si falla de nuevo
        del historial_alertas[nombre]

# Compatibilidad con código antiguo
def procesar_alerta(nombre, valor, limite, unidad):
    procesar_alerta_banda(nombre, valor, -999999, limite, unidad)