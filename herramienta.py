import sqlite3

def inspeccionar_mantenimiento():
    try:
        conn = sqlite3.connect('nexgen_v5_3.db')
        cursor = conn.cursor()
        
        print("🔍 REVISANDO ESTRUCTURA DE 'mantenimiento'...")
        cursor.execute("PRAGMA table_info(mantenimiento)")
        columnas = cursor.fetchall()
        
        if not columnas:
            print("❌ La tabla 'mantenimiento' existe pero está vacía de estructura o hubo un error.")
            return

        for col in columnas:
            # col[1] es el nombre de la columna, col[2] es el tipo (TEXT, INTEGER, etc.)
            print(f"-> Columna: {col[1]} ({col[2]})")
            
        print("\n📊 VISTA PREVIA DE DATOS (Últimos 2):")
        cursor.execute("SELECT * FROM mantenimiento ORDER BY id DESC LIMIT 2")
        rows = cursor.fetchall()
        for row in rows:
            print(row)
            
        conn.close()
    except Exception as e:
        print(f"🔥 Error al consultar: {e}")

inspeccionar_mantenimiento()