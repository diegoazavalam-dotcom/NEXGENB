import paramiko
import sys

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('192.168.100.211', username='raiz', password='Raiz123', timeout=10)
    
    stdin, stdout, stderr = ssh.exec_command('echo Raiz123 | sudo -S docker exec -u 0 nexgen_scada pip install pyasn1==0.4.8')
    sys.stdout.buffer.write(stdout.read())
    sys.stdout.buffer.write(stderr.read())
    
    ssh.exec_command('echo Raiz123 | sudo -S docker compose -f /home/raiz/SCADA_FINAL_1/docker-compose.yml restart scada_core')
    ssh.close()
except Exception as e:
    print(e)
