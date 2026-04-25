import requests
import time

# ---------------------------------------------------------
# PEGA AQUÍ TU TOKEN DEL BOT (El que te dio BotFather)
TOKEN = "8264778812:AAHJXZ-GuDuDv6J9_Lxt162tjDqs4qcFecw" 
# Ejemplo: "123456:ABC-DefGhiJkl..."
# ---------------------------------------------------------

def buscar_id_grupo():
    print(f"🕵️‍♂️ Buscando mensajes recientes para el bot...")
    
    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        if not data.get("ok"):
            print("❌ Error: El Token parece incorrecto.")
            return

        resultados = data.get("result", [])
        
        if not resultados:
            print("⚠️ No encontré mensajes recientes.")
            print("👉 IMPORTANTE: Ve a tu grupo y escribe '/hola' ahora mismo.")
            return

        print("\n✅ HE ENCONTRADO ESTOS CHATS:")
        print("-" * 40)
        
        encontrado = False
        for update in resultados:
            # Buscamos mensajes de grupos
            if "message" in update:
                chat = update["message"]["chat"]
                tipo = chat.get("type")
                titulo = chat.get("title", "Chat Privado")
                chat_id = chat.get("id")
                
                if tipo in ["group", "supergroup"]:
                    print(f"📢 GRUPO DETECTADO: '{titulo}'")
                    print(f"🔑 ID DEL CHAT: {chat_id}") # <--- ESTE ES EL NÚMERO QUE NECESITAS
                    print("-" * 40)
                    encontrado = True
        
        if not encontrado:
            print("Solo encontré mensajes privados, pero no del grupo.")
            print("Asegúrate de que el bot esté en el grupo y escribe algo ahí.")

    except Exception as e:
        print(f"Error de conexión: {e}")

if __name__ == "__main__":
    if "TU_TOKEN" in TOKEN:
        print("❌ ERROR: Edita el archivo y pon tu Token real en la línea 6.")
    else:
        buscar_id_grupo()