import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor, execute_values
import os
import logging
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

# --- CONFIGURACIÓN CENTRALIZADA POSTGRES ---
# Ajusta estos valores a tu configuración de pgAdmin4
DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "database": os.environ.get("DB_NAME", "nexgen_v7"),
    "user": os.environ.get("DB_USER", "postgres"),
    "password": os.environ.get("DB_PASS", ""),
    "port": os.environ.get("DB_PORT", "5432"),
    "client_encoding": "utf8"
}

# --- GESTIÓN DEL POOL DE CONEXIONES ---
try:
    # Creamos un pool de conexiones (Min: 20, Max: 200) para alta concurrencia
    post_pool = psycopg2.pool.SimpleConnectionPool(20, 200, **DB_CONFIG)
    print("✅ DATABASE: Connection Pool de PostgreSQL establecido.")
except Exception as e:
    print(f"🔥 Error Crítico al conectar con PostgreSQL: {e}")
    post_pool = None

def get_db_connection():
    """Obtiene una conexión viva del Pool"""
    if post_pool:
        return post_pool.getconn()
    return None

def release_db_connection(conn):
    """Devuelve la conexión al Pool (Vital para no saturar Postgres)"""
    if post_pool and conn:
        post_pool.putconn(conn)

# --- 1. INICIALIZACIÓN ---

def init_db():
    """Inicializa TODAS las tablas con sintaxis PostgreSQL"""
    conn = get_db_connection()
    if not conn: return
    try:
        with conn.cursor() as cursor:
            # 1. Usuarios (SERIAL en lugar de AUTOINCREMENT)
            cursor.execute('''CREATE TABLE IF NOT EXISTS usuarios 
                  (id SERIAL PRIMARY KEY, username TEXT UNIQUE, password TEXT, role TEXT, grupo TEXT DEFAULT 'PLANTA')''')
            
            # Insertar Admin (ON CONFLICT para evitar errores si ya existe)
            cursor.execute("INSERT INTO usuarios (username, password, role, grupo) VALUES ('admin', '1234', 'ADMIN_TOTAL', 'SISTEMAS') ON CONFLICT (username) DO NOTHING")

            # 2. Configuración Sensores
            cursor.execute('''CREATE TABLE IF NOT EXISTS configuracion_sensores (
                id SERIAL PRIMARY KEY,
                nombre_sensor TEXT UNIQUE,
                id_conexion TEXT,
                tipo_metrica TEXT,
                unidad TEXT,
                db_number INTEGER DEFAULT 1,
                offset_val REAL DEFAULT 0.0,  -- <--- CAMBIADO A REAL PARA SOPORTAR BOOLEANOS (0.5)
                protocolo TEXT DEFAULT 'S7',  -- <--- COLUMNA FALTANTE AGREGADA
                nodo_id TEXT,                 -- <--- COLUMNA FALTANTE AGREGADA
                limite_alerta REAL DEFAULT 100.0,
                x REAL DEFAULT 50.0,
                y REAL DEFAULT 50.0,
                limite_bajo REAL DEFAULT 0.0,
                limite_alto REAL DEFAULT 100.0,
                estado_activo INTEGER DEFAULT 1
            )''')
            
            # 3. Telegram
            cursor.execute('''CREATE TABLE IF NOT EXISTS config_telegram (
                id INTEGER PRIMARY KEY CHECK (id = 1), token TEXT, chat_id TEXT, activo INTEGER DEFAULT 0
            )''')
            cursor.execute("INSERT INTO config_telegram (id, token, chat_id, activo) VALUES (1, '', '', 0) ON CONFLICT (id) DO NOTHING")
            
            # 4. Historial Operativo (TIMESTAMP WITH TIME ZONE)
            cursor.execute('''CREATE TABLE IF NOT EXISTS historial_sensores (
                id BIGSERIAL PRIMARY KEY, nombre_sensor TEXT, valor REAL, fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_fecha ON historial_sensores(fecha)")

            # 5. Tabla de Mantenimiento
            cursor.execute('''CREATE TABLE IF NOT EXISTS mantenimiento 
                              (id SERIAL PRIMARY KEY, 
                               sensor TEXT, operador TEXT, nota TEXT, 
                               fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        
        conn.commit()
        # Llamamos a las sub-iniciaciones
        init_archive_db(conn) # Pasamos conn para reutilizar
        init_incidencias_db(conn)
        init_audit_log(conn)
        print("✅ DATABASE: Sistema PostgreSQL inicializado y sincronizado.")
    except Exception as e:
        print(f"❌ Error en init_db: {e}")
        if conn: conn.rollback()
    finally:
        release_db_connection(conn)

def init_archive_db(conn=None):
    """Crea tabla de archivo (En Postgres usamos una tabla dedicada en la misma DB)"""
    local_conn = False
    if not conn:
        conn = get_db_connection()
        local_conn = True
    try:
        with conn.cursor() as cur:
            cur.execute('''CREATE TABLE IF NOT EXISTS historial_archivo (
                id BIGSERIAL PRIMARY KEY, nombre_sensor TEXT, valor REAL, fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')
        conn.commit()
    finally:
        if local_conn: release_db_connection(conn)

def init_incidencias_db(conn=None):
    local_conn = False
    if not conn:
        conn = get_db_connection()
        local_conn = True
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS log_incidencias (
                    id SERIAL PRIMARY KEY,
                    sensor_id TEXT NOT NULL, valor_detectado REAL NOT NULL, umbral_limite REAL NOT NULL,
                    tipo TEXT DEFAULT 'ALTO', fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    atendido INTEGER DEFAULT 0, comentario_cierre TEXT, usuario_cierre TEXT, fecha_cierre TIMESTAMP,
                    metodo_cierre TEXT DEFAULT 'INDIVIDUAL',
                    prioridad TEXT DEFAULT 'ALTA',
                    estado_ack TEXT DEFAULT 'UNACK',
                    usuario_ack TEXT,
                    fecha_ack TIMESTAMP,
                    shelved_until TIMESTAMP
                )
            """)
            # Hacemos ALTER TABLE por si la tabla ya existía de versiones previas
            try:
                cur.execute("ALTER TABLE log_incidencias ADD COLUMN IF NOT EXISTS prioridad TEXT DEFAULT 'ALTA'")
                cur.execute("ALTER TABLE log_incidencias ADD COLUMN IF NOT EXISTS estado_ack TEXT DEFAULT 'UNACK'")
                cur.execute("ALTER TABLE log_incidencias ADD COLUMN IF NOT EXISTS usuario_ack TEXT")
                cur.execute("ALTER TABLE log_incidencias ADD COLUMN IF NOT EXISTS fecha_ack TIMESTAMP")
                cur.execute("ALTER TABLE log_incidencias ADD COLUMN IF NOT EXISTS shelved_until TIMESTAMP")
            except Exception as e_alter:
                print(f"Nota: {e_alter}")
        conn.commit()
    finally:
        if local_conn: release_db_connection(conn)

def init_audit_log(conn=None):
    local_conn = False
    if not conn:
        conn = get_db_connection()
        local_conn = True
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS log_auditoria (
                    id SERIAL PRIMARY KEY,
                    usuario TEXT,
                    accion TEXT,
                    detalle TEXT,
                    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
        conn.commit()
    finally:
        if local_conn: release_db_connection(conn)

# --- 2. LECTURAS Y TELEMETRÍA ---

def leer_configuracion_sensores():
    conn = get_db_connection()
    try:
        # RealDictCursor devuelve diccionarios reales, compatible con tu frontend
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM configuracion_sensores")
            return cur.fetchall()
    except Exception as e:
        print(f"❌ Error al leer config: {e}")
        return []
    finally:
        release_db_connection(conn)

def obtener_telemetria_frontend():
    """
    Devuelve el estado actual de todos los sensores para el HMI.
    AHORA INCLUYE EL PROTOCOLO (S7 o OPCUA)
    """
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # UNIMOS la configuración con el último valor registrado
            # OJO: Agregué 'c.protocolo' a la selección
            cur.execute("""
                SELECT 
                    c.nombre_sensor as n, 
                    c.id_conexion as id,
                    c.protocolo,  -- <--- ESTO FALTABA
                    c.unidad as u,
                    c.tipo_metrica as m,
                    c.x, c.y,
                    c.limite_bajo as ll,
                    c.limite_alto as lh,
                    c.limite_alerta as l,
                    COALESCE(h.valor, 0) as val
                FROM configuracion_sensores c
                LEFT JOIN (
                    SELECT nombre_sensor, valor 
                    FROM historial_sensores 
                    WHERE id IN (SELECT MAX(id) FROM historial_sensores GROUP BY nombre_sensor)
                ) h ON c.nombre_sensor = h.nombre_sensor
                WHERE c.estado_activo = 1
            """)
            return cur.fetchall()
    except Exception as e:
        print(f"❌ Error Telemetría: {e}")
        return []
    finally:
        release_db_connection(conn)

def obtener_reporte_rango(sensor, inicio, fin):
    conn = get_db_connection()
    try:
        f_inicio = inicio.replace('T', ' ')
        f_fin = fin.replace('T', ' ')
        if len(f_inicio) <= 10: f_inicio += " 00:00:00"
        if len(f_fin) <= 10: f_fin += " 23:59:59"

        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            sql = """
                SELECT valor, fecha FROM (
                    SELECT valor, fecha FROM historial_sensores WHERE nombre_sensor = %s AND fecha >= %s AND fecha <= %s
                    UNION ALL
                    SELECT valor, fecha FROM historial_archivo WHERE nombre_sensor = %s AND fecha >= %s AND fecha <= %s
                ) as datos_combinados
                ORDER BY fecha DESC LIMIT 3000
            """
            cur.execute(sql, (sensor, f_inicio, f_fin, sensor, f_inicio, f_fin))
            rows = cur.fetchall()
        
        # Invertimos los datos para que el gráfico vaya de Izquierda (Viejo) a Derecha (Nuevo)
        rows.reverse()

        # 🚀 ALGORITMO DE DOWNSAMPLING (MUESTREO) 🚀
        if len(rows) > 300:
            salto = len(rows) // 300
            rows = rows[::salto] 

        all_labels = [r['fecha'].strftime("%Y-%m-%d %H:%M") for r in rows]
        all_values = [round(r['valor'], 2) for r in rows]

        return {"labels": all_labels, "values": all_values}
        
    except Exception as e:
        print(f"❌ Error detallado en reporte SQL: {e}")
        return {"labels": [], "values": []}
    finally:
        release_db_connection(conn)

# --- 3. ESCRITURA Y GESTIÓN ---

from license_manager import verificar_licencia

def registrar_nuevo_sensor_completo(d):
    """
    Versión SCADA Resiliente (UPSERT)
    """
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            # 1. Verificar Límite de Licencia antes de insertar un sensor nuevo
            cur.execute("SELECT COUNT(*) FROM configuracion_sensores")
            total_actual = cur.fetchone()[0]
            
            # Ver si el sensor ya existe (para permitir actualizaciones sin gastar nodos)
            cur.execute("SELECT COUNT(*) FROM configuracion_sensores WHERE nombre_sensor = %s", (d['n'],))
            existe = cur.fetchone()[0]
            
            if existe == 0:
                lic = verificar_licencia()
                if lic.get("valida"):
                    max_permitido = lic.get("max_nodos", 10)
                    if total_actual >= max_permitido:
                        raise Exception(f"LÍMITE DE LICENCIA ALCANZADO: Tu licencia {lic.get('nivel')} permite máximo {max_permitido} nodos activos.")

            cur.execute("""
                INSERT INTO configuracion_sensores 
                (nombre_sensor, id_conexion, protocolo, nodo_id, tipo_metrica, unidad, db_number, offset_val, limite_alerta, limite_bajo, limite_alto, estado_activo, x, y)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 1, 50, 50)
                ON CONFLICT (nombre_sensor) DO UPDATE SET
                    db_number = EXCLUDED.db_number,
                    offset_val = EXCLUDED.offset_val,
                    tipo_metrica = EXCLUDED.tipo_metrica,
                    unidad = EXCLUDED.unidad,
                    limite_bajo = EXCLUDED.limite_bajo,
                    limite_alto = EXCLUDED.limite_alto,
                    limite_alerta = EXCLUDED.limite_alerta
            """, (
                d['n'], 
                d['id'], 
                d.get('protocolo', 'S7'), 
                d.get('nodo_id', None), 
                d.get('m', 'REAL'), 
                d.get('u', ''), 
                int(d.get('db', 1)), 
                float(d.get('off', 0.0)), # <--- CORREGIDO A FLOAT
                float(d.get('la', 100.0)), 
                float(d.get('lb', 0.0)), 
                float(d.get('la', 100.0))
            ))
        conn.commit()
        return True
    except Exception as e:
        if conn: conn.rollback()
        print(f"❌ Error registrar sensor: {e}")
        return False
    finally:
        release_db_connection(conn)

def editar_sensor_completo(nombre_original, d):
    """
    Actualiza toda la configuración de un sensor existente en PostgreSQL.
    """
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE configuracion_sensores 
                SET nombre_sensor=%s, id_conexion=%s, protocolo=%s, nodo_id=%s,
                    tipo_metrica=%s, unidad=%s, db_number=%s, offset_val=%s,
                    limite_bajo=%s, limite_alto=%s
                WHERE nombre_sensor=%s
            """, (
                d['n'], 
                d['id'], 
                d.get('protocolo', 'S7'), 
                d.get('nodo_id', None),
                d.get('m', 'REAL'), 
                d.get('u', ''), 
                int(d.get('db', 1)),
                float(d.get('off', 0.0)), # <--- CORREGIDO A FLOAT
                float(d.get('lb', 0.0)), 
                float(d.get('la', 100.0)),
                nombre_original
            ))
            
            if cur.rowcount > 0:
                conn.commit()
                return True
            else:
                conn.rollback()
                return False
    # Agregamos esta captura específica para nombres duplicados
    except psycopg2.IntegrityError: 
        print(f"⚠️ Nombre duplicado al editar: {d['n']}")
        if conn: conn.rollback()
        return False
    except Exception as e:
        print(f"❌ Error al editar sensor: {e}")
        if conn: conn.rollback()
        return False
    finally:
        release_db_connection(conn)

def actualizar_limite_sensor(nombre, valor, tipo="alto"):
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            if tipo == "alto":
                cur.execute("UPDATE configuracion_sensores SET limite_alto=%s, limite_alerta=%s WHERE nombre_sensor=%s", (float(valor), float(valor), nombre))
            else:
                cur.execute("UPDATE configuracion_sensores SET limite_bajo=%s WHERE nombre_sensor=%s", (float(valor), nombre))
        conn.commit()
        return True
    except:
        if conn: conn.rollback()
        return False
    finally: release_db_connection(conn)

def actualizar_posicion_hmi(nombre, x, y):
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("UPDATE configuracion_sensores SET x=%s, y=%s WHERE nombre_sensor=%s", (x, y, nombre))
        conn.commit()
        return True
    except:
        if conn: conn.rollback()
        return False
    finally: release_db_connection(conn)

def eliminar_sensor_db(nombre_sensor):
    """Elimina un sensor de la tabla de configuración"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # Borramos usando el nombre como clave
            cur.execute("DELETE FROM configuracion_sensores WHERE nombre_sensor = %s", (nombre_sensor,))
            
            # Verificamos si realmente se borró algo
            if cur.rowcount > 0:
                conn.commit()
                return True
            else:
                return False # No existía ese nombre
    except Exception as e:
        print(f"❌ Error DB al eliminar sensor: {e}")
        conn.rollback()
        return False
    finally:
        release_db_connection(conn)

def guardar_bloque_telemetria(datos):
    """Guarda en lote usando execute_values para máxima velocidad. (Doble escritura eliminada)"""
    if not datos: return
    conn = get_db_connection()
    if not conn: return
    try:
        with conn.cursor() as cur:
            values = [(d[0], d[1]) for d in datos] # (nombre, valor)
            # Solo escribimos en la tabla principal. El backup se debe hacer con jobs asíncronos.
            execute_values(cur, "INSERT INTO historial_sensores (nombre_sensor, valor) VALUES %s", values)
        conn.commit()
    except Exception as e:
        conn.rollback() # <--- ¡VITAL! Evita que la conexión se pudra en el pool
        print(f"Error guardar bloque: {e}")
    finally:
        release_db_connection(conn)


# --- 4. USUARIOS Y AUTH ---

def validar_usuario(u, p):
    """Valida usuarios con contraseñas encriptadas (Hash)"""
    conn = get_db_connection()
    if not conn: return None
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Traemos el password encriptado de la DB
            cur.execute("SELECT id, username, password, role, grupo FROM usuarios WHERE username=%s", (u,))
            user = cur.fetchone()
            
            if user:
                # Verificamos si el hash coincide O si es el password viejo en texto plano (migración)
                if check_password_hash(user['password'], p) or user['password'] == p:
                    return user
        return None
    except Exception as e:
        print(f"❌ Error en validar_usuario: {e}")
        return None
    finally:
        release_db_connection(conn)

def gestionar_usuario(accion, u, p=None, r=None, g='PLANTA'):
    """Gestión segura de usuarios con Hash de contraseñas"""
    conn = get_db_connection()
    if not conn: return False
    try:
        username_clean = str(u).strip() if u else ""
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            if accion == 'crear':
                # ENCRIPTAMOS LA CONTRASEÑA ANTES DE GUARDARLA
                hashed_pw = generate_password_hash(p)
                cur.execute("INSERT INTO usuarios (username, password, role, grupo) VALUES (%s,%s,%s,%s)", 
                            (username_clean, hashed_pw, r, g))
                conn.commit()
                return True
            elif accion == 'eliminar':
                if username_clean.lower() == 'admin': return False
                cur.execute("DELETE FROM usuarios WHERE username = %s", (username_clean,))
                conn.commit()
                return cur.rowcount > 0
            elif accion == 'listar':
                cur.execute("SELECT id, username, role, grupo FROM usuarios")
                return cur.fetchall()
    except Exception as e:
        if conn: conn.rollback()
        print(f"❌ Error gestionar usuario: {e}")
        return False
    finally:
        release_db_connection(conn)

# --- 5. EXTRAS ---

def config_telegram(accion, data=None, bot_type='operativo'):
    conn = get_db_connection()
    if not conn: return None
    try:
        target_id = 1 if bot_type == 'operativo' else 2
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Aseguramos que exista el registro
            cur.execute("INSERT INTO config_telegram (id, token, chat_id, activo) VALUES (%s, '', '', 0) ON CONFLICT (id) DO NOTHING", (target_id,))
            
            if accion == 'get':
                cur.execute("SELECT token, chat_id, activo FROM config_telegram WHERE id=%s", (target_id,))
                res = cur.fetchone()
                return dict(res) if res else None
                
            elif accion == 'set':
                cur.execute("""
                    UPDATE config_telegram 
                    SET token=%s, chat_id=%s, activo=%s 
                    WHERE id=%s
                """, (data['token'], data['chat_id'], int(data.get('activo', 1)), target_id))
                conn.commit()
                return True
    except Exception as e:
        print(f"❌ Error en config_telegram ({accion}): {e}")
        if conn: conn.rollback()
        return None
    finally:
        release_db_connection(conn)

def obtener_historial_sensor(nombre_sensor, limite=50):
    """
    Recupera historial formateado para Chart.js
    Arregla el error de serialización de fechas de Postgres
    """
    conn = get_db_connection()
    try:
        # Usamos RealDictCursor para poder acceder por nombre (row['valor'])
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute('SELECT fecha, valor FROM historial_sensores WHERE nombre_sensor = %s ORDER BY id DESC LIMIT %s', (nombre_sensor, limite))
            rows = cur.fetchall()

        # PROCESAMIENTO VITAL: Convertir objetos datetime a String
        datos_limpios = []
        for r in rows:
            datos_limpios.append({
                # Formateamos la fecha a hora:min:seg para que el gráfico la entienda
                "fecha": r['fecha'].strftime("%H:%M:%S") if r['fecha'] else "",
                "valor": r['valor']
            })
            
        # Invertimos ([::-1]) para que el gráfico se dibuje de izquierda (viejo) a derecha (nuevo)
        return datos_limpios[::-1] 
        
    except Exception as e:
        print(f"❌ Error obteniendo historial de {nombre_sensor}: {e}")
        return []
    finally:
        release_db_connection(conn)

# --- PEGAR ESTO AL FINAL DE DATABASE.PY SI FALTA ---

def obtener_incidencias_recientes(pagina=1, limite=20):
    """
    Recupera las incidencias paginadas para el panel de alertas.
    Es la función que te estaba dando el AttributeError.
    """
    offset = (pagina - 1) * limite
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Obtenemos los registros
            cur.execute("""
                SELECT id, sensor_id, valor_detectado, umbral_limite, 
                       tipo, fecha, atendido, 
                       comentario_cierre as comentario, usuario_cierre, metodo_cierre
                FROM log_incidencias 
                ORDER BY fecha DESC LIMIT %s OFFSET %s
            """, (limite, offset))
            rows = cur.fetchall()
            
            # Obtenemos el total para calcular páginas
            cur.execute("SELECT COUNT(*) as total FROM log_incidencias")
            total = cur.fetchone()['total']
        
        return {
            "data": [dict(r) for r in rows],
            "total_paginas": (total // limite) + (1 if total % limite > 0 else 0),
            "total_registros": total
        }
    except Exception as e:
        print(f"❌ Error en incidencias recientes: {e}")
        return {"data": [], "total_paginas": 0, "total_registros": 0}
    finally:
        release_db_connection(conn)

def atender_incidencia_db(id_incidencia, usuario, comentario):
    """
    Cierra una incidencia usando PostgreSQL y el Connection Pool.
    Actualiza la tabla log_incidencias cambiando atendido a 1.
    """
    conn = get_db_connection()
    if not conn: 
        return False
        
    try:
        with conn.cursor() as cur:
            # Usamos sintaxis segura de PostgreSQL (%s)
            cur.execute("""
                UPDATE log_incidencias 
                SET atendido = 1, 
                    usuario_cierre = %s, 
                    comentario_cierre = %s,
                    fecha_cierre = CURRENT_TIMESTAMP,
                    metodo_cierre = 'INDIVIDUAL'
                WHERE id = %s 
            """, (usuario, comentario, id_incidencia))
            
            # Verificamos si realmente se actualizó alguna fila
            if cur.rowcount > 0:
                conn.commit()
                return True
            else:
                conn.rollback()
                return False
                
    except Exception as e:
        print(f"❌ Error PostgreSQL al atender incidencia: {e}")
        if conn: conn.rollback()
        return False
    finally:
        release_db_connection(conn)

def obtener_conteos_dashboard():
    """Cuenta nodos activos y alertas pendientes para los badges del menú"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM configuracion_sensores WHERE estado_activo = 1")
            res_nodos = cur.fetchone()
            nodos = res_nodos[0] if res_nodos else 0
            
            cur.execute("SELECT COUNT(*) FROM log_incidencias WHERE atendido = 0")
            res_incidencias = cur.fetchone()
            incidencias = res_incidencias[0] if res_incidencias else 0
            
        return {"nodos": nodos, "incidencias": incidencias}
    except Exception as e:
        print(f"❌ Error conteos: {e}")
        return {"nodos": 0, "incidencias": 0}
    finally:
        release_db_connection(conn)

def atender_incidencias_masivas(sensor_id, usuario, nota):
    """Cierre masivo ISO 9001"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE log_incidencias 
                SET atendido = 1, 
                    comentario_cierre = %s, 
                    usuario_cierre = %s, 
                    fecha_cierre = CURRENT_TIMESTAMP,
                    metodo_cierre = 'MASIVO'
                WHERE sensor_id = %s AND atendido = 0
            """, (f"[CIERRE MASIVO] {nota}", usuario, sensor_id))
            count = cur.rowcount
        conn.commit()
        registrar_evento(usuario, "CIERRE_MASIVO", f"Sensor: {sensor_id} | Alertas cerradas: {count}")
        return count
    except Exception as e:
        print(f"❌ Error en Cierre Masivo DB: {e}")
        return -1
    finally:
        release_db_connection(conn)

# --- AGREGAR AL FINAL DE DATABASE.PY ---

def obtener_auditoria(filtro_fecha=None, filtro_usuario=None, filtro_accion=None):
    """
    Recupera el log de auditoría con filtros y formatea fechas para JSON.
    """
    conn = get_db_connection()
    try:
        # Construcción dinámica de la consulta
        query = "SELECT id, usuario, accion, detalle, fecha FROM log_auditoria WHERE 1=1"
        params = []
        
        # Filtros opcionales
        if filtro_fecha and filtro_fecha.strip():
            query += " AND DATE(fecha) = %s"
            params.append(filtro_fecha)
            
        if filtro_usuario and filtro_usuario.strip():
            query += " AND usuario LIKE %s" # Búsqueda parcial
            params.append(f"%{filtro_usuario}%")
            
        if filtro_accion and filtro_accion.strip():
            query += " AND accion = %s"
            params.append(filtro_accion)
            
        query += " ORDER BY fecha DESC LIMIT 500"
        
        # Ejecución
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, tuple(params))
            rows = cur.fetchall()
            
        # --- PASO CRUCIAL: CONVERSIÓN DE FECHAS ---
        # PostgreSQL devuelve objetos 'datetime', JSON necesita 'strings'
        resultados_limpios = []
        for row in rows:
            d = dict(row)
            if d.get('fecha'):
                # Convertimos a formato "YYYY-MM-DD HH:MM:SS"
                d['fecha'] = d['fecha'].strftime("%Y-%m-%d %H:%M:%S")
            resultados_limpios.append(d)
            
        return resultados_limpios

    except Exception as e:
        print(f"❌ Error leyendo auditoría: {e}")
        return []
    finally:
        release_db_connection(conn)

def registrar_evento(usuario, accion, detalle):
    """
    Escribe un evento en el Log de Auditoría.
    Uso: registrar_evento('admin', 'LOGIN', 'Ingreso al sistema')
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO log_auditoria (usuario, accion, detalle, fecha)
                VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
            """, (usuario, accion, detalle))
        conn.commit()
    except Exception as e:
        print(f"⚠️ Error escribiendo auditoría: {e}")
    finally:
        release_db_connection(conn)

def registrar_incidencia_db(sensor_id, valor, umbral, tipo='ALTO', prioridad='ALTA'):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO log_incidencias 
                (sensor_id, valor_detectado, umbral_limite, tipo, atendido, prioridad, estado_ack) 
                VALUES (%s, %s, %s, %s, 0, %s, 'UNACK')
            """, (sensor_id, valor, umbral, tipo, prioridad))
        conn.commit()
    except Exception as e:
        print(f"❌ Error al registrar incidencia: {e}")
    finally:
        release_db_connection(conn)

def reconocer_alarma(alarma_id, usuario):
    """ISA-18.2: Reconocimiento (Acknowledge) de Alarma Activa"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE log_incidencias 
                SET estado_ack = 'ACK', usuario_ack = %s, fecha_ack = CURRENT_TIMESTAMP
                WHERE id = %s AND estado_ack = 'UNACK'
            """, (usuario, alarma_id))
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ Error al reconocer alarma {alarma_id}: {e}")
        return False
    finally:
        release_db_connection(conn)

def aparcar_alarma(alarma_id, usuario, horas_shelve):
    """ISA-18.2: Supresión Temporal (Shelving) de Alarma"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE log_incidencias 
                SET shelved_until = CURRENT_TIMESTAMP + interval '%s hours',
                    comentario_cierre = %s
                WHERE id = %s AND atendido = 0
            """, (horas_shelve, f"Aparcada por {usuario} ({horas_shelve}h)", alarma_id))
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ Error al aparcar alarma {alarma_id}: {e}")
        return False
    finally:
        release_db_connection(conn)

def obtener_alarmas_isa182():
    """Devuelve las alarmas críticas actuales no cerradas y no silenciadas"""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT * FROM log_incidencias 
                WHERE atendido = 0 
                AND (shelved_until IS NULL OR shelved_until < CURRENT_TIMESTAMP)
                ORDER BY 
                    CASE prioridad
                        WHEN 'CRITICA' THEN 1
                        WHEN 'ALTA' THEN 2
                        WHEN 'MEDIA' THEN 3
                        ELSE 4
                    END,
                    fecha DESC
            """)
            return cur.fetchall()
    except Exception as e:
        print(f"❌ Error al leer alarmas ISA-18.2: {e}")
        return []
    finally:
        release_db_connection(conn)

def obtener_incidencias_pendientes():
    """
    Recupera todas las alertas que no han sido atendidas (atendido = 0).
    Aplica formateo de fecha para compatibilidad con JSON.
    """
    conn = get_db_connection()
    if not conn: 
        return []
        
    try:
        # Usamos RealDictCursor para devolver diccionarios fáciles de convertir a JSON
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT id, sensor_id, valor_detectado, umbral_limite, tipo, fecha 
                FROM log_incidencias 
                WHERE atendido = 0 
                ORDER BY fecha DESC
            """)
            rows = cur.fetchall()
            
            # Formateamos las fechas de PostgreSQL a String
            resultados_limpios = []
            for row in rows:
                d = dict(row)
                if d.get('fecha'):
                    d['fecha'] = d['fecha'].strftime("%Y-%m-%d %H:%M:%S")
                resultados_limpios.append(d)
                
            return resultados_limpios
            
    except Exception as e:
        print(f"❌ Error BD incidencias pendientes: {e}")
        return []
    finally:
        release_db_connection(conn)

# --- REPORTES ESTADÍSTICOS (SPC CARDS) ---

def obtener_reporte_estadistico_sensores():
    """Genera las SPC Cards evaluando estrictamente las últimas 24 horas para evitar cuelgues de CPU"""
    conn = get_db_connection()
    if not conn: return []
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Observa la línea del LEFT JOIN: Limitamos la matemática al último día
            cur.execute("""
                SELECT 
                    c.nombre_sensor as nombre,
                    c.tipo_metrica,
                    c.limite_bajo,
                    c.limite_alto,
                    COUNT(h.valor) as muestreo_total,
                    COALESCE(AVG(h.valor), 0) as media,
                    COALESCE(STDDEV(h.valor), 0) as desviacion,
                    COALESCE(MAX(h.valor) - MIN(h.valor), 0) as rango,
                    -- La lectura es OK si NO es ALTA (>= limite_alto) y NO es BAJA (<= limite_bajo)
                    COUNT(CASE WHEN h.valor < c.limite_alto AND h.valor > c.limite_bajo THEN 1 END) as lecturas_ok
                FROM configuracion_sensores c
                LEFT JOIN historial_sensores h ON c.nombre_sensor = h.nombre_sensor 
                      AND h.fecha >= NOW() - INTERVAL '1 DAY'
                WHERE c.estado_activo = 1
                GROUP BY c.nombre_sensor, c.tipo_metrica, c.limite_bajo, c.limite_alto
            """)
            rows = cur.fetchall()
            
            resultados = []
            for r in rows:
                d = dict(r)
                total = d['muestreo_total']
                
                if d.get('tipo_metrica') == 'BOOL' and d['limite_bajo'] == 0.0 and d['limite_alto'] >= 100.0:
                    estabilidad = 100.0 # Si mantiene los límites por defecto, asumimos 100% estable
                else:
                    estabilidad = (d['lecturas_ok'] / total * 100) if total > 0 else 0
                    
                d['estabilidad'] = round(estabilidad, 1)
                
                d['media'] = round(d['media'], 2)
                d['desviacion'] = round(d['desviacion'], 2)
                d['rango'] = round(d['rango'], 2)
                
                if total == 0:
                    d['nota'] = "SIN DATOS RECIENTES"
                    d['color_nota'] = "text-gray-500"
                    d['color_barra'] = "bg-gray-500"
                elif d['estabilidad'] >= 95:
                    d['nota'] = "PROCESO ESTABLE"
                    d['color_nota'] = "text-green-400"
                    d['color_barra'] = "bg-green-500"
                elif d['estabilidad'] >= 80:
                    d['nota'] = "ALERTA: VARIACIÓN"
                    d['color_nota'] = "text-yellow-400"
                    d['color_barra'] = "bg-yellow-500"
                else:
                    d['nota'] = "CRÍTICO: REVISAR"
                    d['color_nota'] = "text-red-500"
                    d['color_barra'] = "bg-red-500"
                    
                resultados.append(d)
                
            return resultados
    except Exception as e:
        print(f"❌ Error en SPC Cards: {e}")
        return []
    finally:
        release_db_connection(conn)

def ejecutar_mantenimiento_db(dias_retencion_principal=7, dias_retencion_archivo=90):
    """
    Traslada datos antiguos de la tabla principal al archivo
    y elimina datos del archivo más antiguos que el límite.
    Ideal para ejecutar una vez al día a las 3:00 AM.
    """
    conn = get_db_connection()
    if not conn: return False
    try:
        with conn.cursor() as cur:
            # 1. Mover datos viejos al archivo (más de 'dias_retencion_principal' días)
            cur.execute("""
                INSERT INTO historial_archivo (nombre_sensor, valor, fecha)
                SELECT nombre_sensor, valor, fecha
                FROM historial_sensores
                WHERE fecha < NOW() - (%s * INTERVAL '1 day');
            """, (dias_retencion_principal,))
            
            # 2. Borrar esos mismos datos de la tabla principal
            cur.execute("""
                DELETE FROM historial_sensores
                WHERE fecha < NOW() - (%s * INTERVAL '1 day');
            """, (dias_retencion_principal,))
            
            # 3. Eliminar permanentemente datos muy viejos del archivo
            cur.execute("""
                DELETE FROM historial_archivo
                WHERE fecha < NOW() - (%s * INTERVAL '1 day');
            """, (dias_retencion_archivo,))
            
        conn.commit()
        print("✅ DATABASE: Mantenimiento y Poda de datos ejecutados correctamente.")
        return True
    except Exception as e:
        conn.rollback()
        print(f"❌ Error en mantenimiento de DB: {e}")
        return False
    finally:
        release_db_connection(conn)