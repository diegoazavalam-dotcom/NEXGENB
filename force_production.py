import paramiko
import sys

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('192.168.100.211', username='raiz', password='Raiz123', timeout=10)
    
    # We will modify gateway_service.py to always read 'production' or just hardcode it to True for now
    ssh.exec_command('echo Raiz123 | sudo -S sed -i "s/MODO_PRODUCCION = os.environ.get(\'FLASK_ENV\') == \'production\'/MODO_PRODUCCION = True/" /home/raiz/SCADA_FINAL_1/gateway_service.py')
    
    # Restart the container so it picks up the change
    ssh.exec_command('echo Raiz123 | sudo -S docker compose -f /home/raiz/SCADA_FINAL_1/docker-compose.yml restart scada_core')
    
    ssh.close()
except Exception as e:
    print(e)
