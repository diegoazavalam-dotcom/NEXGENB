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

database.init_db()

nodos_snmp = [
    # Mapeo: ID apunta a localhost (127.0.0.1) o la IP del agente SNMP en Linux
    # El offset_val determina la métrica según snmp_covert_agent.py (1.0=CPU, 2.0=RAM, 3.0=DISK)
    {"n": "Linux_CPU_Usage", "id": "127.0.0.1:161", "protocolo": "SNMP", "m": "REAL", "u": "%", "db": 1, "off": 1.0, "la": 85.0, "lb": 0.0, "lh": 95.0},
    {"n": "Linux_RAM_Usage", "id": "127.0.0.1:161", "protocolo": "SNMP", "m": "REAL", "u": "%", "db": 1, "off": 2.0, "la": 80.0, "lb": 0.0, "lh": 90.0},
    {"n": "Linux_Disk_Usage", "id": "127.0.0.1:161", "protocolo": "SNMP", "m": "REAL", "u": "%", "db": 1, "off": 3.0, "la": 90.0, "lb": 0.0, "lh": 95.0}
]

print("Inyectando nodos SNMP (Hardware Monitor)...")
for s in nodos_snmp:
    try:
        conn = database.get_db_connection()
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO configuracion_sensores 
                (nombre_sensor, id_conexion, protocolo, tipo_metrica, unidad, db_number, offset_val, limite_alerta, limite_bajo, limite_alto, estado_activo, x, y)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 1, 50, 50)
                ON CONFLICT (nombre_sensor) DO UPDATE SET
                    protocolo = EXCLUDED.protocolo, id_conexion = EXCLUDED.id_conexion, offset_val = EXCLUDED.offset_val
            """, (s['n'], s['id'], s['protocolo'], s['m'], s['u'], s['db'], s['off'], s['la'], s['lb'], s['lh']))
        conn.commit()
        print(f"✅ Nodo SNMP creado: {s['n']}")
    except Exception as e:
        if conn: conn.rollback()
        print(f"❌ Error al crear nodo {s['n']}: {e}")
    finally:
        database.release_db_connection(conn)

print("\nListo. El Gateway ahora intentará leer CPU, RAM y Disco por SNMP.")
