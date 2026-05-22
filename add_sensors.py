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

# Inicializar DB si no existe
database.init_db()

sensores = [
    {"n": "Gas_Honeywell_1", "id": "192.168.0.10", "protocolo": "S7", "m": "REAL", "u": "%", "db": 100, "off": 10.0, "la": 20.0, "lb": 0.0},
    {"n": "Gas_Honeywell_2", "id": "192.168.0.10", "protocolo": "S7", "m": "REAL", "u": "%", "db": 100, "off": 14.0, "la": 20.0, "lb": 0.0},
    {"n": "Gas_Honeywell_3", "id": "192.168.0.10", "protocolo": "S7", "m": "REAL", "u": "%", "db": 100, "off": 18.0, "la": 20.0, "lb": 0.0},
    {"n": "Gas_Honeywell_4", "id": "192.168.0.10", "protocolo": "S7", "m": "REAL", "u": "%", "db": 100, "off": 22.0, "la": 20.0, "lb": 0.0}
]

print("Insertando Sensores de Gas...")
for s in sensores:
    # Omitimos verificación de licencia inyectando directo para asegurar el setup base
    try:
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
        print(f"✅ Sensor {s['n']} agregado/actualizado correctamente.")
    except Exception as e:
        if conn: conn.rollback()
        print(f"❌ Error al agregar {s['n']}: {e}")
    finally:
        database.release_db_connection(conn)

print("\n--- TEST GATEWAY Y DB ---")
print("Sensores activos leídos por el frontend:")
telemetria = database.obtener_telemetria_frontend()
for t in telemetria:
    print(f"- {t['n']} (DB{t.get('db_number', 100)}.DBD{t.get('offset_val', 0)}) -> {t['val']}{t['u']}")
