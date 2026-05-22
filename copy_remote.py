import paramiko
import os

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('192.168.100.211', username='raiz', password='Raiz123', timeout=10)
    
    sftp = ssh.open_sftp()
    sftp.get('/home/raiz/SCADA_FINAL_1/app.py', 'C:\\SCADA_FINAL_1\\app.py.remote')
    sftp.close()
    ssh.close()
    print("Successfully copied app.py from remote VM to local C:\\SCADA_FINAL_1\\app.py.remote")
except Exception as e:
    print(e)
