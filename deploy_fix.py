import paramiko
from scp import SCPClient
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    ssh.connect('192.168.100.48', username='raiz', password='Raiz123')
    with SCPClient(ssh.get_transport()) as scp:
        scp.put('C:\\SCADA_FINAL_1\\requirements.txt', '/home/raiz/SCADA_FINAL_1/requirements.txt')
        
    stdin, stdout, stderr = ssh.exec_command('cd ~/SCADA_FINAL_1 && sudo -S docker compose build --no-cache && sudo -S docker compose up -d')
    stdin.write('Raiz123\n')
    stdin.flush()
    for line in stdout:
        print(line.strip().encode('ascii', 'replace').decode('ascii'))
except Exception as e:
    print(e)
finally:
    ssh.close()
