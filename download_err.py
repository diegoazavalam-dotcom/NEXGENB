import paramiko
import os

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('192.168.100.211', username='raiz', password='Raiz123', timeout=10)
    
    sftp = ssh.open_sftp()
    sftp.get('/tmp/err.log', 'C:\\SCADA_FINAL_1\\err.log')
    sftp.close()
    ssh.close()
    print("Downloaded err.log")
except Exception as e:
    print(e)
