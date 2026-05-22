import tkinter as tk
from tkinter import messagebox, simpledialog, scrolledtext
import webbrowser
import sys
import os
import psycopg2
from license_manager import verificar_licencia, LICENSE_FILE

def check_and_wizard(db_config):
    """
    Verifica la conexión a PostgreSQL y la licencia. Si algo falla, muestra un asistente gráfico (Tkinter)
    para guiar al usuario a configurarlo.
    Devuelve True si ambos son exitosos. Si el usuario cancela, sale del programa.
    """
    postgres_ok = False
    licencia_ok = False
    lic_info = verificar_licencia()

    if lic_info.get("valida", False):
        licencia_ok = True

    try:
        # Intentamos conectar a la base de datos "postgres" genérica primero para ver si el motor existe
        test_config = db_config.copy()
        test_config['database'] = 'postgres'
        conn = psycopg2.connect(**test_config)
        conn.close()
        
        # Ahora intentamos conectar a nuestra DB específica
        try:
            conn2 = psycopg2.connect(**db_config)
            conn2.close()
        except psycopg2.OperationalError as e:
            if "database" in str(e) and "does not exist" in str(e):
                # Si el motor existe pero la DB no, la creamos silenciosamente
                conn = psycopg2.connect(**test_config)
                conn.autocommit = True
                cursor = conn.cursor()
                cursor.execute(f"CREATE DATABASE {db_config['database']}")
                cursor.close()
                conn.close()
        postgres_ok = True
    except psycopg2.OperationalError as e:
        # Falló la conexión al motor completamente
        postgres_ok = False

    if postgres_ok and licencia_ok:
        return True
        
    lanzar_interfaz_wizard(db_config, postgres_ok, licencia_ok, lic_info)
    return False

def lanzar_interfaz_wizard(db_config, postgres_ok, licencia_ok, lic_info):
    root = tk.Tk()
    root.title("NexGen SCADA - Asistente de Instalación")
    root.geometry("600x480")
    root.configure(bg="#0f172a") # Slate-900 Tailwind
    
    # Centrar en pantalla
    root.eval('tk::PlaceWindow . center')
    
    # Título
    lbl_title = tk.Label(root, text="Asistente de Configuración NexGen", 
                         font=("Arial", 16, "bold"), fg="#38bdf8", bg="#0f172a")
    lbl_title.pack(pady=20)
    
    # Estado PostgreSQL
    pg_color = "#4ade80" if postgres_ok else "#ef4444"
    pg_text = "✅ Motor PostgreSQL Detectado" if postgres_ok else "❌ Motor PostgreSQL No Encontrado"
    lbl_pg = tk.Label(root, text=pg_text, font=("Arial", 12, "bold"), fg=pg_color, bg="#0f172a")
    lbl_pg.pack(pady=5)
    
    if not postgres_ok:
        desc_pg = ("NexGen SCADA requiere PostgreSQL v15+ para operar en modo industrial.\n"
                   f"(Host: {db_config['host']} | Pto: {db_config['port']} | Usr: {db_config['user']})\n"
                   "Por favor instala PostgreSQL o ingresa credenciales válidas.")
        tk.Label(root, text=desc_pg, font=("Arial", 10), fg="#94a3b8", bg="#0f172a", justify="center").pack(pady=5)
    
    # Estado Licencia
    lic_color = "#4ade80" if licencia_ok else "#ef4444"
    lic_text = "✅ Licencia Válida" if licencia_ok else "❌ Licencia Inválida o Faltante"
    lbl_lic = tk.Label(root, text=lic_text, font=("Arial", 12, "bold"), fg=lic_color, bg="#0f172a")
    lbl_lic.pack(pady=5)
    
    if not licencia_ok:
        msg = lic_info.get("error", "Requiere archivo license.key válido.")
        tk.Label(root, text=msg, font=("Arial", 10), fg="#f87171", bg="#0f172a", justify="center").pack(pady=5)
    
    def descargar_pg():
        webbrowser.open("https://www.enterprisedb.com/downloads/postgres-postgresql-downloads")
        messagebox.showinfo("Instrucción", 
            "1. Descarga e instala PostgreSQL.\n"
            "2. Durante la instalación, cuando pida contraseña, pon: Root123\n"
            "3. Deja el puerto por defecto (5432).\n\n"
            "Al terminar la instalación, vuelve a abrir el SCADA.", parent=root)
        root.destroy()
        sys.exit(0)
        
    def cambiar_password():
        pwd = simpledialog.askstring("Credenciales", "Si tienes PostgreSQL con otra contraseña, ingrésala:", parent=root)
        if pwd:
            messagebox.showinfo("Atención", 
                "Para actualizar la contraseña, debes editar database.py o pedir una versión compilada con tu contraseña.\n"
                f"Contraseña ingresada: {pwd}", parent=root)
            root.destroy()
            sys.exit(0)
            
    def ingresar_licencia():
        top = tk.Toplevel(root)
        top.title("Ingresar Llave de Licencia")
        top.geometry("400x300")
        top.configure(bg="#0f172a")
        top.eval('tk::PlaceWindow . center')
        
        tk.Label(top, text="Pega aquí el contenido de tu licencia:", fg="white", bg="#0f172a", font=("Arial", 11)).pack(pady=10)
        txt = scrolledtext.ScrolledText(top, width=45, height=10)
        txt.pack(padx=10, pady=5)
        
        def guardar():
            content = txt.get("1.0", tk.END).strip()
            if content:
                with open(LICENSE_FILE, "w") as f:
                    f.write(content)
                messagebox.showinfo("Guardado", "Licencia guardada. Por favor reinicia el SCADA.", parent=top)
                root.destroy()
                sys.exit(0)
        
        tk.Button(top, text="Guardar y Reiniciar", bg="#3b82f6", fg="white", font=("Arial", 10, "bold"), command=guardar).pack(pady=10)

    def salir():
        root.destroy()
        sys.exit(0)

    # Botones
    btn_frame = tk.Frame(root, bg="#0f172a")
    btn_frame.pack(pady=20)
    
    if not postgres_ok:
        tk.Button(btn_frame, text="⬇️ Instalar PostgreSQL", font=("Arial", 10, "bold"), bg="#3b82f6", fg="white", 
                  padx=10, pady=5, cursor="hand2", command=descargar_pg).grid(row=0, column=0, padx=5, pady=5)
        tk.Button(btn_frame, text="🔑 Cambiar Contraseña DB", font=("Arial", 10, "bold"), bg="#475569", fg="white", 
                  padx=10, pady=5, cursor="hand2", command=cambiar_password).grid(row=0, column=1, padx=5, pady=5)
    
    if not licencia_ok:
        tk.Button(btn_frame, text="🛡️ Ingresar Licencia", font=("Arial", 10, "bold"), bg="#f59e0b", fg="white", 
                  padx=10, pady=5, cursor="hand2", command=ingresar_licencia).grid(row=1, column=0, columnspan=2, pady=5)
    
    tk.Button(root, text="Salir", font=("Arial", 10), bg="#1e293b", fg="#94a3b8", 
              relief="flat", cursor="hand2", command=salir).pack(side=tk.BOTTOM, pady=20)
    
    root.mainloop()
