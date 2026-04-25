import sqlite3
import requests

def diagnostico_telegram():
    print("🕵️‍♂️ INICIANDO DIAGNÓSTICO DE TELEGRAM...")
    print("-" * 40)
    
    # 1. LEER DATOS DE LA BASE DE DATOS
    try:
        conn = sqlite3.connect('nexgen_v5_3.db')
        cursor = conn.cursor()
        cursor.execute("SELECT token, chat_id, activo FROM config_telegram WHERE id=1")
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            print("❌ ERROR GRAVE: La tabla 'config_telegram' está vacía o no existe.")
            return

        token, chat_id, activo = row
        
        # Mostramos los datos (ocultando parte del token por seguridad)
        token_visible = token[:5] + "..." if token else "VACÍO"
        
        print(f"📋 CONFIGURACIÓN EN BD:")
        print(f"   ► Token:    {token_visible}")
        print(f"   ► Chat ID:  {chat_id}")
        print(f"   ► Activo:   {'✅ SÍ (1)' if activo else '❌ NO (0)'}")
        
        # VALIDACIONES PREVIAS
        if not activo:
            print("\n⚠️ ALERTA: El sistema está DESACTIVADO en el panel.")
            print("   👉 Entra a la web -> Botón Notificaciones -> Activa el switch.")
        
        if not token or not chat_id:
            print("\n❌ ERROR: Faltan el Token o el Chat ID.")
            return

        # 2. INTENTO DE ENVÍO REAL
        print("\n🚀 INTENTANDO CONECTAR CON SERVIDORES DE TELEGRAM...")
        
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        mensaje = "🔔 NEXGEN SCADA: Prueba de conexión exitosa.\nSi lees esto, el sistema funciona."
        payload = {"chat_id": chat_id, "text": mensaje}
        
        response = requests.post(url, json=payload, timeout=10)
        
        # 3. ANÁLISIS DEL RESULTADO
        if response.status_code == 200:
            print("\n✅ ¡ÉXITO TOTAL!")
            print("   El mensaje fue entregado. Revisa tu celular.")
            print("   Si el script funciona pero la app no, reinicia 'python app.py'.")
        elif response.status_code == 401:
            print("\n❌ ERROR 401: NO AUTORIZADO")
            print("   El Token del bot es incorrecto. Verifica que no tenga espacios extra.")
        elif response.status_code == 400:
            print("\n❌ ERROR 400: PETICIÓN INCORRECTA")
            print("   Probablemente el Chat ID está mal o el bot no ha iniciado conversación contigo.")
        else:
            print(f"\n❌ ERROR {response.status_code}:")
            print(f"   Respuesta: {response.text}")

    except Exception as e:
        print(f"\n❌ ERROR DE EJECUCIÓN: {e}")

if __name__ == '__main__':
    diagnostico_telegram()