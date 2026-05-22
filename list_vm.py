import paramiko

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('192.168.100.211', username='raiz', password='Raiz123', timeout=10)
    stdin, stdout, stderr = ssh.exec_command('ls -la /home/raiz/SCADA_FINAL_1/')
    print(stdout.read().decode('utf-8'))
    ssh.close()
except Exception as e:
    print(e)
