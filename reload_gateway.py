import paramiko
import sys

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('192.168.100.211', username='raiz', password='Raiz123', timeout=10)
    
    # Reload gateway config
    script = "import urllib.request; req=urllib.request.Request('http://127.0.0.1:5006/reload_config', method='POST'); print(urllib.request.urlopen(req).read().decode())"
    stdin, stdout, stderr = ssh.exec_command(f'echo Raiz123 | sudo -S docker exec nexgen_scada python3 -c "{script}"')
    sys.stdout.buffer.write(stdout.read())
    
    # Check status again
    script = "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:5006/status').read().decode())"
    stdin, stdout, stderr = ssh.exec_command(f'echo Raiz123 | sudo -S docker exec nexgen_scada python3 -c "{script}"')
    sys.stdout.buffer.write(stdout.read())
    
    ssh.close()
except Exception as e:
    print(e)
