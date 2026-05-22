import paramiko
import sys

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('192.168.100.211', username='raiz', password='Raiz123', timeout=10)
    
    stdin, stdout, stderr = ssh.exec_command('cat /home/raiz/SCADA_FINAL_1/gateway_service.py | grep MODO')
    sys.stdout.buffer.write(stdout.read())
    
    ssh.close()
except Exception as e:
    print(e)
