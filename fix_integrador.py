import paramiko
import sys

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('192.168.100.211', username='raiz', password='Raiz123', timeout=10)
    
    # Let's fix integrador.html
    cmd = """echo Raiz123 | sudo -S sed -i "s|fetch('/api/telemetria')|fetch('/api/telemetria', { headers: { 'X-API-Key': token } })|g" /home/raiz/SCADA_FINAL_1/templates/integrador.html"""
    ssh.exec_command(cmd)
    
    # We don't even need to restart docker for HTML files if they are in volumes, but we do it anyway just in case
    # Actually wait, templates might be cached? If so, we restart
    print("Restarting docker container...")
    ssh.exec_command('cd ~/SCADA_FINAL_1 && echo Raiz123 | sudo -S docker compose restart scada_core')
    print("Done")
    ssh.close()
except Exception as e:
    print(e)
