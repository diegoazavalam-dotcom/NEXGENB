import paramiko

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('192.168.100.211', username='raiz', password='Raiz123', timeout=10)
    
    print("Recreating docker container...")
    stdin, stdout, stderr = ssh.exec_command('cd ~/SCADA_FINAL_1 && echo Raiz123 | sudo -S docker compose up -d --force-recreate')
    print(stdout.read().decode('utf-8'))
    print(stderr.read().decode('utf-8'))
    print("Done")
    
    ssh.close()
except Exception as e:
    print(e)
