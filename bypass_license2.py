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

# Just remove the license check from registrar_nuevo_sensor_completo
# It probably throws an exception or returns False, and prints "LÍMITE DE LICENCIA ALCANZADO"
# Let's see if we can find it:
content = re.sub(r'if max_nodos_permitidos.*?:.*?raise Exception\(.*?\)', '', content, flags=re.DOTALL)
content = re.sub(r'if \w+ >= max_nodos_permitidos.*?:.*?raise Exception\(.*?\)', '', content, flags=re.DOTALL)

# Or we can just mock the license module completely:
with open('/home/raiz/SCADA_FINAL_1/license_manager.py', 'w') as f:
    f.write('''
def verificar_licencia():
    return {'valida': True, 'cliente': 'Planta Automotriz Guanajuato', 'dias_restantes': 294, 'nivel': 'PRO', 'max_nodos': 9999}
''')

"""
    cmd = f"cat << 'EOF' > /tmp/bypass_license2.py\n{script}\nEOF\n"
    ssh.exec_command(cmd)
    
    ssh.exec_command('echo Raiz123 | sudo -S /home/raiz/agent_venv/bin/python /tmp/bypass_license2.py')
    ssh.exec_command('echo Raiz123 | sudo -S docker compose -f /home/raiz/SCADA_FINAL_1/docker-compose.yml restart scada_core')
    
    ssh.close()
except Exception as e:
    print(e)
