from flask import Flask, render_template, jsonify, request, session, send_file, redirect, url_for
from werkzeug.utils import secure_filename
import pandas as pd
import os
import shutil
from io import BytesIO
from datetime import datetime, timedelta
from urllib.parse import unquote
from functools import wraps

# --- IMPORTACIONES LOCALES ---
import database  
from config import SENSORES
from sensor_gateway import SensorGateway 
from license_manager import verificar_licencia
from config_manager import leer_config_maestra, guardar_config_maestra

# Variable global para no leer el archivo en CADA click (optimización de I/O)
ESTADO_LICENCIA = {"revisado_en": None, "data": None}

# 1. LEER LA CONFIGURACIÓN MAESTRA
CONFIG_SISTEMA = leer_config_maestra()

# Tu contraseña secreta de integrador (cámbiala por algo seguro)
GOD_MODE_TOKEN = "LeoyZoe0822"

# Configuración de alertas
try:
    import alerts
except ImportError:
    alerts = None

app = Flask(__name__)
#app.secret_key = 'CLAVE_SECRETA_SCADA' 
app.secret_key = "12345_NEXGEN_FIXED"
app.permanent_session_lifetime = timedelta(days=7)

# --- CONFIGURACIÓN ---
MODO_PRODUCCION = True  
DB_NAME = 'nexgen_v5_3.db'

# INICIALIZACIÓN DEL GATEWAY (Patrón Singleton)
# Nota: La inyección de IP se debe hacer dentro de SensorGateway en tu V1.1
gateway = SensorGateway(modo_produccion=MODO_PRODUCCION)

# --- DECORADOR DE SEGURIDAD (FIX) ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Verificamos user_id que es lo que seteamos en el login
        if 'user_id' not in session:
            if request.path.startswith('/api/'):
                return jsonify({"status": "error", "message": "Sesion expirada"}), 401
            # Si es una ruta de página (dashboard, reports), mandamos al index
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# --- RUTAS OCULTAS: GOD MODE ---
@app.route('/panel-integrador')
def vista_god_mode():
    return render_template('integrador.html')

@app.route('/api/godmode/config', methods=['GET', 'POST'])
def god_mode_config():
    # 1. VERIFICACIÓN DE SEGURIDAD
    token_recibido = request.headers.get('X-GodMode-Token')
    if token_recibido != GOD_MODE_TOKEN:
        return jsonify({"error": "Acceso denegado. Protocolo Integrador requerido."}), 403

    # 2. SI ES UN GET: Devolvemos la configuración
    if request.method == 'GET':
        config_actual = leer_config_maestra()
        return jsonify(config_actual)

    # 3. SI ES UN POST: Guardamos y aplicamos Hot Reload
    if request.method == 'POST':
        nueva_data = request.json
        if guardar_config_maestra(nueva_data):
            
            # 🔥 HOT RELOAD DEL PLC SIN REINICIAR 🔥
            # Navegamos dentro del JSON: nueva_data -> 'plc' -> 'ip'
            datos_plc = nueva_data.get('plc', {})
            nueva_ip = datos_plc.get('ip')
            
            # Verificamos que el gateway tenga el driver cargado y le pasamos la IP
            if nueva_ip and hasattr(gateway, 'driver') and hasattr(gateway.driver, 'actualizar_conexion'):
                print(f"⚡ Ejecutando Hot Reload hacia IP: {nueva_ip}")
                gateway.driver.actualizar_conexion(nueva_ip)
                
            # Opcional: Recargar los sensores si se modificaron desde GodMode
            sensores_db = database.leer_configuracion_sensores()
            if sensores_db:
                gateway.cargar_configuracion(sensores_db)

            return jsonify({"status": "success", "message": "Configuración y Red actualizadas en caliente."})
        else:
            return jsonify({"status": "error", "message": "Fallo al escribir en disco"}), 500

# --- MIDDLEWARE (PROTECCIÓN Y SESIONES) ---
@app.before_request
def make_session_permanent():
    session.permanent = True

@app.before_request
def escudo_licencia():
    # EXENTAMOS LAS RUTAS CRÍTICAS Y EL PANEL INTEGRADOR
    rutas_libres = ['static', 'licencia_expirada', 'upload_license', 'vista_god_mode', 'god_mode_config']
    if request.endpoint in rutas_libres:
        return
        
    global ESTADO_LICENCIA
    ahora = datetime.now()
    
    # ⚠️ MODO DE PRUEBA: Lee el archivo físico en CADA clic (Caché desactivado)
    ESTADO_LICENCIA["data"] = verificar_licencia()
    ESTADO_LICENCIA["revisado_en"] = ahora
    
    print(f"🕵️ [ESCUDO] Evaluando ruta: {request.path}")
    print(f"📊 [ESCUDO] Datos de la llave: {ESTADO_LICENCIA['data']}")
        
    if not ESTADO_LICENCIA["data"].get("valida", False):
        print("🚫 [ESCUDO] ¡LLAVE INVÁLIDA! Bloqueando acceso...")
        if not request.path.startswith('/api/'):
            return redirect(url_for('licencia_expirada'))
        else:
            return jsonify({"status": "error", "message": "PAYMENT_REQUIRED", "detalle": ESTADO_LICENCIA["data"]["error"]}), 402
            
    print("✅ [ESCUDO] Acceso Permitido.")

# --- RUTAS DE LICENCIA ---
@app.route('/licencia_expirada')
def licencia_expirada():
    global ESTADO_LICENCIA
    mensaje = ESTADO_LICENCIA["data"].get("error", "Licencia inválida")
    return render_template('licencia.html', mensaje=mensaje)

@app.route('/upload_license', methods=['POST'])
def upload_license():
    if 'license_file' not in request.files:
        return "No se envió ningún archivo", 400
        
    archivo = request.files['license_file']
    if archivo.filename == '':
        return "El archivo está vacío", 400
        
    if archivo and archivo.filename.endswith('.key'):
        ruta_destino = os.path.join(app.root_path, 'license.key')
        archivo.save(ruta_destino)
        
        global ESTADO_LICENCIA
        ESTADO_LICENCIA["revisado_en"] = None
        return redirect(url_for('index'))
        
    return "Formato de archivo no permitido. Debe ser .key", 400

# --- RUTAS DE NAVEGACIÓN Y STATUS ---
@app.route('/')
def index(): 
    return render_template('index.html', modo_produccion=MODO_PRODUCCION)

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', modo_produccion=MODO_PRODUCCION)

@app.route('/reports')
@login_required
def reports():
    return render_template('reports.html')

@app.route('/api/plc/status')
def get_plc_status():
    """1. Consulta el estado al Gateway"""
    is_alive = gateway.driver.get_connected_status()
    return jsonify({
        "status": "ONLINE" if is_alive else "OFFLINE",
        "color": "text-green-500" if is_alive else "text-red-500",
        "timestamp": datetime.now().strftime('%H:%M:%S')
    })

# --- GESTIÓN DE AUTENTICACIÓN ---
@app.route('/api/auth/check')
def check_auth():
    if 'user_id' in session:
        return jsonify({
            "logged_in": True,
            "username": session.get('username'),
            "role": session.get('rol') or session.get('role'), 
            "grupo": session.get('grupo')
        })
    return jsonify({"logged_in": False, "role": None})

@app.route('/api/auth/login', methods=['POST'])
def login():
    try:
        data = request.json
        user = database.validar_usuario(data.get('username'), data.get('password'))

        if user:
            session.clear() 
            session.permanent = True
            
            session['user_id'] = str(user.get('id') or user.get('username'))
            session['username'] = user.get('username')
            session['role'] = user.get('role')
            session['rol'] = user.get('role') 
            session['grupo'] = user.get('grupo', 'PLANTA')

            database.registrar_evento(user['username'], 'LOGIN', 'Acceso exitoso')
            
            return jsonify({
                "status": "success", 
                "logged_in": True,
                "username": user['username'],
                "role": user['role']
            }), 200
        
        return jsonify({"status": "error", "message": "Credenciales incorrectas"}), 401
    except Exception as e:
        print(f"🔥 ERROR EN LOGIN: {e}") 
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/kill')
def kill_session():
    session.clear()
    return "Sesión eliminada. <a href='/'>Volver al inicio</a>"

# --- TELEMETRÍA ---
@app.route('/api/telemetria')
@login_required 
def api_telemetria():
    try:
        datos = database.obtener_telemetria_frontend() 
        if datos is None:
            datos = []
            
        conteos = database.obtener_conteos_dashboard()
        total_incidencias = conteos.get('incidencias', 0)
        total_nodos = conteos.get('nodos', 0)
            
        return jsonify({
            "sensores": datos, 
            "total_incidencias": total_incidencias, 
            "total_nodos_activos": total_nodos,
            "status": "ok"
        })
        
    except Exception as e:
        print(f"🔥 Error en API Telemetría: {e}")
        return jsonify({
            "sensores": [], 
            "total_incidencias": 0, 
            "total_nodos_activos": 0,
            "error": str(e)
        }), 500
    
# --- REPORTES Y ANALÍTICA ---
@app.route('/api/reportes/spc_cards')
@login_required 
def api_spc_cards():
    try:
        datos = database.obtener_reporte_estadistico_sensores()
        return jsonify({"status": "success", "data": datos})
    except Exception as e:
        print(f"🔥 Error en API SPC Cards: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# --- ADMINISTRACIÓN DE USUARIOS ---
@app.route('/api/admin/usuarios', methods=['GET', 'POST', 'DELETE'])
@login_required
def users_route():
    if request.method == 'GET':
        try:
            usuarios_db = database.gestionar_usuario('listar', None)
            return jsonify([dict(u) for u in usuarios_db])
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    if request.method == 'POST':
        try:
            d = request.json
            usuario_nuevo = d.get('username')
            rol_nuevo = d.get('role')
            
            exito = database.gestionar_usuario('crear', usuario_nuevo, d.get('password'), rol_nuevo, d.get('grupo', 'PLANTA'))
            
            if exito:
                admin_actual = session.get('username', 'Sistema')
                detalle = f"Creó usuario: {usuario_nuevo} (Rol: {rol_nuevo})"
                database.registrar_evento(admin_actual, 'USER_MGMT', detalle)
                return jsonify({"status": "success"})
            
            return jsonify({"error": "Error al crear (¿Usuario duplicado?)"}), 400
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    if request.method == 'DELETE':
        try:
            username = request.args.get('username', '').strip()
            admin_actual = session.get('username', 'Sistema')
            if username == admin_actual:
                return jsonify({"error": "No puedes eliminar tu propia cuenta"}), 403

            if database.gestionar_usuario('eliminar', username):
                database.registrar_evento(admin_actual, 'USER_MGMT', f"Eliminó usuario: {username}")
                return jsonify({"status": "success"})
            
            return jsonify({"error": "Error al eliminar (¿Usuario no existe?)"}), 404
        except Exception as e:
            return jsonify({"error": str(e)}), 500

# --- CONFIGURACIÓN DE SENSORES Y HMI ---
@app.route('/api/admin/config_sensores', methods=['GET', 'POST'])
@login_required 
def route_config_sensores():
    if request.method == 'GET':
        try:
            rows = database.leer_configuracion_sensores()
            return jsonify({"sensores": [dict(r) for r in rows]})
        except Exception as e:
            print(f"❌ Error GET sensores: {e}")
            return jsonify({"error": str(e)}), 500
    
    if request.method == 'POST':
        try:
            data = request.json 
            if database.registrar_nuevo_sensor_completo(data):
                usuario = session.get('username', 'Sistema')
                proto = data.get('protocolo', 'S7')
                detalle = f"Creó sensor: {data.get('n')} (Proto: {proto})"
                database.registrar_evento(usuario, 'CONFIG_CHANGE', detalle)
                return jsonify({"status": "success"})
            
            return jsonify({"error": "No se pudo guardar. Verifique si el nombre ya existe."}), 400
        except Exception as e:
            print(f"🔥 Error CRÍTICO en POST config_sensores: {e}")
            return jsonify({"error": str(e)}), 500

@app.route('/api/admin/editar_sensor', methods=['POST'])
@login_required
def route_editar_sensor():
    try:
        data = request.json
        nombre_original = data.get('original_n')
        
        if not nombre_original:
            return jsonify({"error": "Falta el nombre original del sensor"}), 400

        if database.editar_sensor_completo(nombre_original, data):
            usuario = session.get('username', 'Sistema')
            database.registrar_evento(usuario, 'CONFIG_CHANGE', f"Editó sensor: {nombre_original}")
            
            sensores_db = database.leer_configuracion_sensores()
            if sensores_db:
                gateway.cargar_configuracion(sensores_db)
                
            return jsonify({"status": "success"})
            
        return jsonify({"error": "No se pudo actualizar (¿Nombre duplicado?)"}), 400
    except Exception as e:
        print(f"🔥 Error CRÍTICO editando sensor: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/eliminar_sensor', methods=['POST'])
@login_required
def route_eliminar_sensor():
    try:
        data = request.json
        nombre = data.get('n')
        
        if not nombre:
            return jsonify({"error": "Falta el nombre del sensor"}), 400

        if database.eliminar_sensor_db(nombre):
            usuario = session.get('username', 'Sistema')
            database.registrar_evento(usuario, 'CONFIG_CHANGE', f"Eliminó sensor: {nombre}")
            return jsonify({"status": "success"})
        
        return jsonify({"error": "No se pudo eliminar (¿El sensor existe?)"}), 400
    except Exception as e:
        print(f"🔥 Error CRÍTICO eliminando sensor: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/update_low_limit', methods=['POST'])
@login_required
def update_low_limit():
    d = request.json
    if database.actualizar_limite_sensor(d['n'], d['v'], "bajo"): 
        gateway.cargar_configuracion(database.leer_configuracion_sensores())
        return jsonify({"status": "success"})
    return jsonify({"error": "Error DB"}), 500

@app.route('/api/admin/update_high_limit', methods=['POST'])
@login_required
def update_high_limit():
    d = request.json
    if database.actualizar_limite_sensor(d['n'], d['v'], "alto"): 
        gateway.cargar_configuracion(database.leer_configuracion_sensores())
        return jsonify({"status": "success"})
    return jsonify({"error": "Error DB"}), 500

@app.route('/api/admin/update_position', methods=['POST'])
@login_required
def update_position():
    d = request.json
    if database.actualizar_posicion_hmi(d['n'], d['x'], d['y']): return jsonify({"status": "success"})
    return jsonify({"error": "Error DB"}), 500

@app.route('/api/admin/telegram', methods=['GET', 'POST'])
@login_required
def telegram_route():
    if request.method == 'GET': 
        return jsonify(database.config_telegram('get'))
    
    if database.config_telegram('set', request.json):
        if alerts: 
            alerts.recargar_config() 
            print("🚀 Motor de Telegram recargado con nuevas credenciales")
        return jsonify({"status": "success"})
    return jsonify({"error": "Error DB"}), 500

# --- MANTENIMIENTO E INCIDENCIAS ---
@app.route('/api/incidencias/recientes')
@login_required
def route_incidencias_recientes():
    pagina = request.args.get('p', 1, type=int)
    resultado = database.obtener_incidencias_recientes(pagina=pagina)
    
    if isinstance(resultado, list):
        return jsonify({
            "data": resultado,
            "total_paginas": 1 
        })
    return jsonify(resultado)

@app.route('/api/incidencias/atender', methods=['POST'])
@login_required
def route_atender_js():
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400
            
        idx = data.get('id')
        comentario = data.get('comentario', 'Sin comentario')
        usuario = session.get('username', 'OPERADOR')

        if database.atender_incidencia_db(idx, usuario, comentario):
            database.registrar_evento(usuario, 'INCIDENCIA_CERRADA', f"Cerró incidencia ID: {idx} | Nota: {comentario}")
            return jsonify({"success": True}), 200
        else:
            return jsonify({"success": False, "error": "No se encontró la incidencia o falló la BD"}), 500

    except Exception as e:
        print(f"🔥 ERROR CRÍTICO AL ATENDER: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/incidencias/atender_masivo', methods=['POST'])
@login_required
def route_atender_masivo():
    data = request.json
    usuario = session.get('username', 'ADMIN_SCADA')
    cantidad = database.atender_incidencias_masivas(data.get('sensor_id'), usuario, data.get('comentario'))
    return jsonify({"success": True, "mensaje": f"Se cerraron {cantidad} registros"})

@app.route('/api/dashboard/stats')
@login_required
def route_dashboard_stats():
    stats = database.obtener_conteos_dashboard()
    return jsonify({"n": stats['nodos'], "i": stats['incidencias']})

@app.route('/api/admin/auditoria')
@login_required
def get_audit_log():
    try:
        f = request.args.get('f')
        u = request.args.get('u')
        a = request.args.get('a')
        
        logs = database.obtener_auditoria(filtro_fecha=f, filtro_usuario=u, filtro_accion=a)
        
        # Envolvemos en un diccionario para respetar la estructura previa
        return jsonify({"logs": logs})
    except Exception as e:
        print(f"Error API Audit: {e}")
        return jsonify({"logs": []}), 500

@app.route('/api/incidencias/pendientes')
@login_required
def get_incidencias_pendientes():
    return jsonify(database.obtener_incidencias_pendientes())

# --- REPORTES Y EXPORTACIÓN ---
@app.route('/api/reportes/data_masiva', methods=['POST'])
@login_required
def get_reporte_masivo():
    try:
        data = request.json
        nombres = data.get('sensores', [])
        inicio, fin = data.get('inicio'), data.get('fin')
        paquete_sensores, todas_las_labels = [], []
        for n in nombres:
            res_db = database.obtener_reporte_rango(n, inicio, fin)
            paquete_sensores.append({"sensor": n, "values": res_db['values']})
            if not todas_las_labels: todas_las_labels = res_db['labels']
        return jsonify({"success": True, "labels": todas_las_labels, "datasets": paquete_sensores})
    except Exception as e: return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/exportar/incidentes')
@login_required
def exportar_incidentes():
    conn = database.get_db_connection()
    if not conn:
        return jsonify({"error": "Sin conexión a DB"}), 500
        
    query = """
        SELECT 
            sensor_id AS "SENSOR", 
            valor_detectado AS "LECTURA", 
            umbral_limite AS "UMBRAL", 
            tipo AS "TIPO", 
            fecha AS "DETECCION", 
            fecha_cierre AS "CIERRE",
            (fecha_cierre - fecha) AS "TIEMPO_RESPUESTA",
            usuario_cierre AS "OPERADOR", 
            metodo_cierre AS "TIPO_CIERRE", 
            comentario_cierre AS "NOTA"
        FROM log_incidencias 
        WHERE atendido = 1 
        ORDER BY fecha DESC
    """
    
    try:
        with conn.cursor() as cur:
            cur.execute(query)
            rows = cur.fetchall()
            column_names = [desc[0] for desc in cur.description]
            
        database.release_db_connection(conn)

        df = pd.DataFrame(rows, columns=column_names)

        if not df.empty:
            df['DETECCION'] = df['DETECCION'].astype(str)
            df['CIERRE'] = df['CIERRE'].astype(str)
            df['TIEMPO_RESPUESTA'] = df['TIEMPO_RESPUESTA'].astype(str)

        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Audit_Trail_ISO')
            
            worksheet = writer.sheets['Audit_Trail_ISO']
            for i, col in enumerate(df.columns):
                column_len = max(df[col].astype(str).str.len().max(), len(col)) + 2
                worksheet.set_column(i, i, column_len)

        output.seek(0)
        
        return send_file(
            output, 
            as_attachment=True, 
            download_name=f"Audit_Trail_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
    except Exception as e:
        if conn:
            database.release_db_connection(conn)
        print(f"🔥 Error en reporte Excel: {e}")
        return f"Error en reporte Excel: {str(e)}", 500

@app.route('/api/reportes/excel_masivo')
@login_required
def exportar_excel_masivo():
    sensores = request.args.getlist('sensores')
    inicio, fin = request.args.get('inicio'), request.args.get('fin')
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        for s in sensores:
            res = database.obtener_reporte_rango(s, inicio, fin)
            df = pd.DataFrame({'Fecha': res['labels'], 'Valor': res['values'], 'Sensor': s})
            df.to_excel(writer, index=False, sheet_name=s[:31])
    output.seek(0)
    return send_file(output, as_attachment=True, download_name="Reporte_Masivo_Correlacion.xlsx")

@app.route('/api/exportar/sensor')
@login_required
def exportar_excel_safe():
    try:
        nombre_raw = request.args.get('nombre', '')
        nombre_buscado = unquote(nombre_raw).replace("Tendencia: ", "").strip()
        datos = database.obtener_historial_sensor(nombre_buscado, limite=1000)
        df = pd.DataFrame([dict(f) for f in datos]) if datos else pd.DataFrame({'Estado': ['Sin datos']})
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Historial')
        output.seek(0)
        return send_file(output, as_attachment=True, download_name=f"Data_{nombre_buscado}.xlsx")
    except Exception as e: return f"Error: {str(e)}", 500

@app.route('/api/historial/<nombre>')
@login_required
def api_historial(nombre):
    try:
        inicio = request.args.get('inicio')
        fin = request.args.get('fin')
        
        if inicio and fin:
            datos = database.obtener_reporte_rango(nombre, inicio, fin)
            return jsonify(datos)
        else:
            raw_datos = database.obtener_historial_sensor(nombre, limite=100)
            labels = [d['fecha'] for d in raw_datos]
            values = [d['valor'] for d in raw_datos]
            return jsonify({"labels": labels, "values": values})
            
    except Exception as e:
        print(f"Error en API Historial: {e}")
        return jsonify({"labels": [], "values": []}), 500

@app.route('/api/admin/upload_plano', methods=['POST'])
@login_required
def upload_plano():
    if 'file' not in request.files: 
        return jsonify({"error": "No hay archivo"}), 400
    
    file = request.files['file']
    if file.filename == '': 
        return jsonify({"error": "Archivo vacío"}), 400

    try:
        filename = secure_filename(file.filename)
        ext = os.path.splitext(filename)[1].lower()
        if not ext: ext = '.jpg'
        
        nuevo_nombre = f'layout_bg{ext}'
        folder = os.path.join(app.root_path, 'static', 'img')
        
        if not os.path.exists(folder):
            os.makedirs(folder)
            
        target_path = os.path.join(folder, nuevo_nombre)
        file.save(target_path)
        
        return jsonify({"status": "success", "path": f"/static/img/{nuevo_nombre}"})
    except Exception as e:
        print(f"🔥 Error físico al guardar: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/backup_db')
@login_required
def download_backup():
    # Al estar en PostgreSQL, no podemos enviar un archivo .db como en SQLite.
    # Se debe notificar al usuario que la BD es industrial.
    return jsonify({
        "status": "info",
        "message": "Sistema corriendo en PostgreSQL. Los respaldos se gestionan automáticamente en el servidor vía pg_dump. Contacte a Soporte IT."
    }), 400

@app.route('/reparar_db')
def reparar_db():
    conn = database.get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS configuracion_sensores;")
        conn.commit()
        database.release_db_connection(conn)
        
        database.init_db()
        return "<h1>✅ Tabla de sensores eliminada y recreada con éxito.</h1><p>Ya puedes regresar al SCADA y agregar tus tanques.</p>"
    except Exception as e:
        return f"<h1>❌ Error al reparar: {e}</h1>"

# =====================================================================
# --- ARRANQUE (¡ESTO DEBE SER ESTRICTAMENTE LO ÚLTIMO EN TU ARCHIVO!) ---
# =====================================================================

if __name__ == '__main__':
    import sys
    import traceback
    
    try:
        # 1. Parche de Rutas para PyInstaller (Evita el crash de la línea 314)
        if getattr(sys, 'frozen', False):
            # Si estamos corriendo como .exe, usamos la carpeta real del sistema
            base_dir = os.path.dirname(sys.executable)
        else:
            # Si estamos en Python crudo
            base_dir = os.path.dirname(os.path.abspath(__file__))
            
        ruta_img = os.path.join(base_dir, 'static', 'img')
        os.makedirs(ruta_img, exist_ok=True)
        
        # 2. Inicialización de Base de Datos
        database.init_db()
        database.init_incidencias_db()
        
        # 3. Carga de Hardware
        sensores_db = database.leer_configuracion_sensores()
        if sensores_db:
            gateway.cargar_configuracion(sensores_db)
        
        # 4. Arranque de Motores
        gateway.start()
        print("🚀 Motor SCADA Iniciado correctamente.")
        print("🌐 Servidor web escuchando en http://localhost:5005")
        
        # IMPORTANTE: debug=False es OBLIGATORIO en la versión compilada
        app.run(debug=False, host='0.0.0.0', port=5005, use_reloader=False)

    except Exception as e:
        # 🔥 EL ESCUDO ANTI-CIERRE 🔥
        # Si algo falla, atrapamos el error y evitamos que el .exe se cierre de golpe
        print("\n" + "="*50)
        print("🚨 ERROR FATAL EN EL ARRANQUE DEL SISTEMA 🚨")
        print("="*50)
        traceback.print_exc()  # Esto imprimirá la línea exacta y la causa real
        print("="*50)
        input("\nPresiona la tecla ENTER para salir...")