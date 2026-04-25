import sqlite3

def ver_usuarios():
    try:
        # Conectamos a tu base de datos real
        conn = sqlite3.connect('nexgen_v5_3.db')
        cursor = conn.cursor()
        
        print("--- BUSCANDO USUARIOS EN BASE DE DATOS ---")
        
        # 1. Verificamos si la tabla existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='usuarios';")
        if not cursor.fetchone():
            print("❌ ERROR: No existe la tabla 'usuarios'. Tu base de datos está vacía o nueva.")
            print("👉 SOLUCIÓN: Necesitas registrar un usuario nuevo desde cero.")
            return

        # 2. Listamos los usuarios (sin mostrar contraseñas encriptadas si tienen hash)
        cursor.execute("SELECT * FROM usuarios")
        usuarios = cursor.fetchall()
        
        if not usuarios:
            print("⚠️ La tabla existe pero ESTÁ VACÍA. No hay usuarios creados.")
        else:
            print(f"✅ Se encontraron {len(usuarios)} usuarios:")
            for u in usuarios:
                # Ajusta los índices según las columnas de tu tabla
                print(f"👤 Usuario: {u}") 

    except Exception as e:
        print(f"❌ Error leyendo base de datos: {e}")
    finally:
        if 'conn' in locals(): conn.close()

if __name__ == '__main__':
    ver_usuarios()