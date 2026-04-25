import sqlite3
import os

# CONFIGURACIÓN DE SENSORES INICIAL
SENSORES = [
    {"n": "Vibración", "x": 10, "y": 45, "u": "mm/s", "l": 4.0},
    {"n": "Humedad", "x": 18, "y": 25, "u": "%HR", "l": 65},
    {"n": "Temperatura", "x": 32, "y": 45, "u": "°C", "l": 75},
    {"n": "Nivel", "x": 40, "y": 25, "u": "%", "l": 90},
    {"n": "Proximidad", "x": 48, "y": 45, "u": "mm", "l": 45},
    {"n": "Presión", "x": 58, "y": 45, "u": "Bar", "l": 12},
    {"n": "Gas_Aire", "x": 50, "y": 12, "u": "ppm", "l": 80},
    {"n": "Flujo", "x": 80, "y": 60, "u": "L/m", "l": 100}
]

DB_NAME = 'nexgen_v5_3.db'

def crear_base_datos():
    # 1. Limpieza inicial (Opcional, borra si existe)
    if os.path.exists(DB_NAME):
        try:
            os.remove(DB_NAME)
            print("🗑️ Base de datos antigua eliminada.")
        except:
            print("⚠️ No se pudo borrar el archivo (quizás está en uso).")

    # 2. Conexión
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    print("🛠️ Creando tablas...")

    # Tabla Usuarios
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            usuario TEXT UNIQUE, 
            password TEXT, 
            rol TEXT, 
            grupo TEXT DEFAULT 'PLANTA'
        )
    ''')
    # Usuario Admin
    cursor.execute("INSERT OR IGNORE INTO usuarios (usuario, password, rol) VALUES ('admin', '1234', 'ADMIN_TOTAL')")

    # Tabla Configuración Sensores
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS configuracion_sensores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_sensor TEXT UNIQUE,
            id_conexion TEXT,
            tipo_metrica TEXT DEFAULT 'REAL',
            unidad TEXT,
            x REAL DEFAULT 50.0,
            y REAL DEFAULT 50.0,
            limite_alerta REAL DEFAULT 100.0,
            estado_activo INTEGER DEFAULT 1
        )
    ''')

    # Tabla Historial
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS historial_sensores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_sensor TEXT,
            valor REAL,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 3. Sembrar datos
    print("🌱 Sembrando sensores...")
    for s in SENSORES:
        cursor.execute("""
            INSERT OR IGNORE INTO configuracion_sensores 
            (nombre_sensor, id_conexion, unidad, x, y, limite_alerta)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (s['n'], s['n'], s['u'], s['x'], s['y'], s['l']))

    conn.commit()
    conn.close()
    print("✅ ¡BASE DE DATOS CREADA EXITOSAMENTE!")
    print("👉 Ahora puedes ejecutar: python app.py")

if __name__ == '__main__':
    crear_base_datos()