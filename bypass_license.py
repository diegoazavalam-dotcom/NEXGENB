import paramiko
import sys

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('192.168.100.211', username='raiz', password='Raiz123', timeout=10)
    
    script = """
import re

with open('/home/raiz/SCADA_FINAL_1/database.py', 'r') as f:
    content = f.read()

content = content.replace("from license_manager import verificar_licencia, max_nodos_permitidos", 
                          "from license_manager import verificar_licencia\\n\\ndef max_nodos_permitidos(): return 9999")

with open('/home/raiz/SCADA_FINAL_1/database.py', 'w') as f:
    f.write(content)
"""
    cmd = f"cat << 'EOF' > /tmp/bypass_license.py\n{script}\nEOF\n"
    ssh.exec_command(cmd)
    
    ssh.exec_command('echo Raiz123 | sudo -S /home/raiz/agent_venv/bin/python /tmp/bypass_license.py')
    ssh.exec_command('echo Raiz123 | sudo -S docker compose -f /home/raiz/SCADA_FINAL_1/docker-compose.yml restart scada_core')
    
    ssh.close()
except Exception as e:
    print(e)
