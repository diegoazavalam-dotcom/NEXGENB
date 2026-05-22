import paramiko

route_code = """
@app.route('/api/godmode/update_agent', methods=['GET', 'POST'])
def godmode_update_agent():
    token_recibido = request.headers.get('X-GodMode-Token')
    if token_recibido != GOD_MODE_TOKEN:
        return jsonify({"error": "Acceso denegado"}), 403

    if request.method == 'GET':
        config_actual = leer_config_maestra()
        agente = config_actual.get('agente_zole', {})
        return jsonify(agente)

    if request.method == 'POST':
        nueva_data = request.json
        config_actual = leer_config_maestra()
        config_actual['agente_zole'] = nueva_data
        guardar_config_maestra(config_actual)
        
        # Guardar limites en DB
        limites = nueva_data.get('limites', {})
        if limites:
            if limites.get('cpu_h') and limites.get('cpu_l'):
                database.actualizar_limite_sensor('Linux_CPU_Usage', float(limites['cpu_h']), 'alto')
                database.actualizar_limite_sensor('Linux_CPU_Usage', float(limites['cpu_l']), 'bajo')
            if limites.get('ram_h') and limites.get('ram_l'):
                database.actualizar_limite_sensor('Linux_RAM_Usage', float(limites['ram_h']), 'alto')
                database.actualizar_limite_sensor('Linux_RAM_Usage', float(limites['ram_l']), 'bajo')
            if limites.get('disk_h') and limites.get('disk_l'):
                database.actualizar_limite_sensor('Linux_Disk_Usage', float(limites['disk_h']), 'alto')
                database.actualizar_limite_sensor('Linux_Disk_Usage', float(limites['disk_l']), 'bajo')
                
        # Guardar telegram si existe
        telegram = nueva_data.get('telegram', {})
        if telegram:
            database.config_telegram('set', telegram)
            if alerts:
                alerts.recargar_config()
                
        sensores_db = database.leer_configuracion_sensores()
        if sensores_db:
            gateway.cargar_configuracion(sensores_db)
            
        return jsonify({"status": "success"})
"""

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('192.168.100.211', username='raiz', password='Raiz123', timeout=10)
    
    # We will inject this right before # --- MIDDLEWARE (PROTECCIÓN Y SESIONES) --- in app.py
    # Since python sed can be tricky with multiline, we will use python script on the remote to do the insertion
    
    remote_script = f"""
import sys

with open('/home/raiz/SCADA_FINAL_1/app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if '# --- MIDDLEWARE (PROTECCIÓN Y SESIONES) ---' in line:
        new_lines.append('''{route_code}''')
    new_lines.append(line)

with open('/home/raiz/SCADA_FINAL_1/app.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
"""
    cmd = f"cat << 'EOF' > /tmp/fix_app.py\n{remote_script}EOF\n"
    ssh.exec_command(cmd)
    
    stdin, stdout, stderr = ssh.exec_command('echo Raiz123 | sudo -S python3 /tmp/fix_app.py')
    print(stdout.read().decode('utf-8'))
    print(stderr.read().decode('utf-8'))
    
    print("Restarting docker container...")
    ssh.exec_command('cd ~/SCADA_FINAL_1 && echo Raiz123 | sudo -S docker compose restart scada_core')
    print("Done")
    ssh.close()
except Exception as e:
    print(e)
