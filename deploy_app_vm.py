import paramiko
from scp import SCPClient

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print("Connecting...")
    ssh.connect('192.168.100.211', username='raiz', password='Raiz123', timeout=10)
    
    print("Uploading app.py...")
    with SCPClient(ssh.get_transport()) as scp:
        scp.put(r'C:\Users\betoo\Downloads\SCADA_FINAL_1-20260422T040553Z-3-001\SCADA_FINAL_1\app.py', '/home/raiz/SCADA_FINAL_1/app.py')
        
    print("Restarting docker container...")
    stdin, stdout, stderr = ssh.exec_command('cd ~/SCADA_FINAL_1 && echo Raiz123 | sudo -S docker compose restart scada_core')
    print(stdout.read().decode('utf-8'))
    print(stderr.read().decode('utf-8'))
    print("Done")
    ssh.close()
except Exception as e:
    print(e)
