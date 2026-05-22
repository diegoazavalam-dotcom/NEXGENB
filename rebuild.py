import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    ssh.connect('192.168.100.48', username='raiz', password='Raiz123')
    stdin, stdout, stderr = ssh.exec_command('cd ~/SCADA_FINAL_1 && echo Raiz123 | sudo -S docker compose build --no-cache && echo Raiz123 | sudo -S docker compose up -d')
    for line in stdout:
        print(line.strip('\n'))
    for line in stderr:
        print("ERR:", line.strip('\n'))
except Exception as e:
    print(e)
finally:
    ssh.close()
