import paramiko
import sys

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('192.168.100.211', username='raiz', password='Raiz123', timeout=10)
    
    sftp = ssh.open_sftp()
    sftp.get('/home/raiz/SCADA_FINAL_1/sensor_gateway.py', 'C:\\SCADA_FINAL_1\\sensor_gateway.py.remote')
    sftp.close()
    ssh.close()
    print("Downloaded sensor_gateway.py")
except Exception as e:
    print(e)
