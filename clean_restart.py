import paramiko
import sys

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('192.168.100.211', username='raiz', password='Raiz123', timeout=10)
    
    # KILL EVERYTHING that matches gateway_service.py and app.py
    stdin, stdout, stderr = ssh.exec_command('echo Raiz123 | sudo -S pkill -f gateway_service.py')
    ssh.exec_command('echo Raiz123 | sudo -S pkill -f "python app.py"')
    
    # Also stop and start docker compose properly
    ssh.exec_command('echo Raiz123 | sudo -S docker compose -f /home/raiz/SCADA_FINAL_1/docker-compose.yml down')
    ssh.exec_command('echo Raiz123 | sudo -S docker compose -f /home/raiz/SCADA_FINAL_1/docker-compose.yml up -d')
    
    ssh.close()
except Exception as e:
    print(e)
