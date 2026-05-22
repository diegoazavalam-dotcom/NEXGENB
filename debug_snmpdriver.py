import paramiko
import sys

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('192.168.100.211', username='raiz', password='Raiz123', timeout=10)
    
    stdin, stdout, stderr = ssh.exec_command('echo Raiz123 | sudo -S docker exec nexgen_scada sed -i "s/self.connected = False/self.connected = False\\n        print(f\\"SNMPDriver INIT: simulation={simulation}, PYSNMP_INSTALLED={PYSNMP_INSTALLED}, self.simulation={self.simulation}\\")/g" /app/plc_driver.py')
    sys.stdout.buffer.write(stdout.read())
    
    # Reload gateway
    reload_cmd = "import urllib.request; req=urllib.request.Request('http://127.0.0.1:5006/reload_config', method='POST'); print(urllib.request.urlopen(req).read().decode())"
    stdin, stdout, stderr = ssh.exec_command(f'echo Raiz123 | sudo -S docker exec nexgen_scada python3 -c "{reload_cmd}"')
    sys.stdout.buffer.write(stdout.read())
    
    ssh.close()
except Exception as e:
    print(e)
