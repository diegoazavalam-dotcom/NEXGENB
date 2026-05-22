import paramiko
import sys

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('192.168.100.211', username='raiz', password='Raiz123', timeout=10)
    
    script = """
import re

with open('/home/raiz/SCADA_FINAL_1/plc_driver.py', 'r') as f:
    content = f.read()

# Replace self.simulation = False with self.simulation = True in SNMPDriver
content = re.sub(r'class SNMPDriver\(BaseGateway\):\s+def __init__\(self, ip, port=161, community=\'public\', simulation=True\):\s+self\.ip = ip\s+self\.port = port\s+self\.community = community\s+self\.simulation = False',
                 '''class SNMPDriver(BaseGateway):
    def __init__(self, ip, port=161, community='public', simulation=True):
        self.ip = ip
        self.port = port
        self.community = community
        self.simulation = True''', content)

with open('/home/raiz/SCADA_FINAL_1/plc_driver.py', 'w') as f:
    f.write(content)
"""
    cmd = f"cat << 'EOF' > /tmp/fix_snmp.py\n{script}\nEOF\n"
    ssh.exec_command(cmd)
    
    ssh.exec_command('echo Raiz123 | sudo -S /home/raiz/agent_venv/bin/python /tmp/fix_snmp.py')
    ssh.exec_command('echo Raiz123 | sudo -S docker compose -f /home/raiz/SCADA_FINAL_1/docker-compose.yml restart scada_core')
    
    ssh.close()
except Exception as e:
    print(e)
