import sqlite3

def reparar():
    conn = sqlite3.connect('nexgen_v5_3.db')
    cursor = conn.cursor()
    
    print("🛠️ Iniciando reparación de base de datos...")

    # 1. Crear la tabla de grupos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS grupos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT UNIQUE NOT NULL,
            descripcion TEXT
        )
    ''')
    
    # 2. Insertar grupos iniciales
    grupos = [('SISTEMAS', 'Admin IT'), ('PLANTA', 'Operación General')]
    cursor.executemany("INSERT OR IGNORE INTO grupos (nombre, descripcion) VALUES (?, ?)", grupos)
    
    # 3. Asegurar que la tabla usuarios tenga la columna 'grupo'
    try:
        cursor.execute("ALTER TABLE usuarios ADD COLUMN grupo TEXT DEFAULT 'PLANTA'")
        print("✅ Columna 'grupo' añadida a usuarios.")
    except sqlite3.OperationalError:
        print("ℹ️ La columna 'grupo' ya existía en usuarios.")

    conn.commit()
    conn.close()
    print("🚀 Reparación completada. La tabla 'grupos' ya existe.")

if __name__ == "__main__":
    reparar()