import paramiko
import sys

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('192.168.100.211', username='raiz', password='Raiz123', timeout=10)
    
    sftp = ssh.open_sftp()
    sftp.get('/home/raiz/SCADA_FINAL_1/gateway_service.py', 'C:\\SCADA_FINAL_1\\gateway_service.py.remote')
    sftp.close()
    ssh.close()
    print("Downloaded gateway_service.py")
except Exception as e:
    print(e)
