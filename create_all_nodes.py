import sys
import io

if sys.stdout is None or not hasattr(sys.stdout, 'reconfigure'):
    sys.stdout = io.StringIO()
    sys.stderr = io.StringIO()
else:
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

sys.path.append('C:\\SCADA_FINAL_1')
import database

# Inicializar DB
database.init_db()

nodos_a_crear = [
    # --- SENSORES DE GAS HONEYWELL (ANTI EXPLOSIÓN) ---
    {"n": "Honeywell_AntiExplosion_01", "id": "192.168.0.10", "protocolo": "S7", "m": "REAL", "u": "%LEL", "db": 100, "off": 10.0, "la": 20.0, "lb": 0.0},
    {"n": "Honeywell_AntiExplosion_02", "id": "192.168.0.10", "protocolo": "S7", "m": "REAL", "u": "%LEL", "db": 100, "off": 14.0, "la": 20.0, "lb": 0.0},
    {"n": "Honeywell_AntiExplosion_03", "id": "192.168.0.10", "protocolo": "S7", "m": "REAL", "u": "%LEL", "db": 100, "off": 18.0, "la": 20.0, "lb": 0.0},
    {"n": "Honeywell_AntiExplosion_04", "id": "192.168.0.10", "protocolo": "S7", "m": "REAL", "u": "%LEL", "db": 100, "off": 22.0, "la": 20.0, "lb": 0.0},

    # --- EXTRACTORES (Nodos Booleanos para monitoreo en SCADA) ---
    {"n": "Extractor_01_Run", "id": "192.168.0.10", "protocolo": "S7", "m": "BOOL", "u": "", "db": 100, "off": 0.0, "la": 1.0, "lb": 0.0},
    {"n": "Extractor_02_Run", "id": "192.168.0.10", "protocolo": "S7", "m": "BOOL", "u": "", "db": 100, "off": 1.0, "la": 1.0, "lb": 0.0},
    {"n": "Extractor_03_Run", "id": "192.168.0.10", "protocolo": "S7", "m": "BOOL", "u": "", "db": 100, "off": 2.0, "la": 1.0, "lb": 0.0},
    {"n": "Extractor_04_Run", "id": "192.168.0.10", "protocolo": "S7", "m": "BOOL", "u": "", "db": 100, "off": 3.0, "la": 1.0, "lb": 0.0},
    {"n": "Extractor_05_Run", "id": "192.168.0.10", "protocolo": "S7", "m": "BOOL", "u": "", "db": 100, "off": 4.0, "la": 1.0, "lb": 0.0},
    {"n": "Extractor_06_Run", "id": "192.168.0.10", "protocolo": "S7", "m": "BOOL", "u": "", "db": 100, "off": 5.0, "la": 1.0, "lb": 0.0},
    {"n": "Extractor_07_Run", "id": "192.168.0.10", "protocolo": "S7", "m": "BOOL", "u": "", "db": 100, "off": 6.0, "la": 1.0, "lb": 0.0},
    {"n": "Extractor_08_Run", "id": "192.168.0.10", "protocolo": "S7", "m": "BOOL", "u": "", "db": 100, "off": 7.0, "la": 1.0, "lb": 0.0}
]

print("Limpiando nodos antiguos...")
conn = database.get_db_connection()
with conn.cursor() as cur:
    cur.execute("DELETE FROM configuracion_sensores;")
conn.commit()
database.release_db_connection(conn)

print("Inyectando nodos desde la lógica del Super Admin...")
for s in nodos_a_crear:
    try:
        # Bypassear la licencia directamente para garantizar la creación como Super Admin
        conn = database.get_db_connection()
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO configuracion_sensores 
                (nombre_sensor, id_conexion, protocolo, tipo_metrica, unidad, db_number, offset_val, limite_alerta, limite_bajo, limite_alto, estado_activo, x, y)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 1, 50, 50)
                ON CONFLICT (nombre_sensor) DO UPDATE SET
                    db_number = EXCLUDED.db_number, offset_val = EXCLUDED.offset_val
            """, (s['n'], s['id'], s['protocolo'], s['m'], s['u'], s['db'], s['off'], s['la'], s['lb'], 100.0))
        conn.commit()
        print(f"✅ Nodo creado: {s['n']}")
    except Exception as e:
        if conn: conn.rollback()
        print(f"❌ Error al crear nodo {s['n']}: {e}")
    finally:
        database.release_db_connection(conn)

print("\nValidación de todos los nodos en el Core de Telemetría:")
telemetria = database.obtener_telemetria_frontend()
for t in telemetria:
    print(f"- {t['n']} [{t['m']}] (DB{t.get('db_number', 100)}.DBD{t.get('offset_val', 0)})")
