import psycopg2

try:
    conn = psycopg2.connect(
        host="192.168.100.211",
        database="nexgen_v7",
        user="postgres",
        password="Root123",
        port=5432
    )
    cursor = conn.cursor()
    cursor.execute("UPDATE usuarios SET password = 'LeoyZoe0822' WHERE username = 'admin'")
    conn.commit()
    print("Contraseña actualizada exitosamente.")
    conn.close()
except Exception as e:
    print(f"Error: {e}")
