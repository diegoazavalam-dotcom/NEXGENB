import paramiko
import sys

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('192.168.100.211', username='raiz', password='Raiz123', timeout=10)
    
    # Let's fix plc_driver.py locally in host and cp to container
    cmd = """
echo Raiz123 | sudo -S sed -i 's/self.simulation = simulation or not PYSNMP_INSTALLED/self.simulation = False/' /home/raiz/SCADA_FINAL_1/plc_driver.py
echo Raiz123 | sudo -S docker cp /home/raiz/SCADA_FINAL_1/plc_driver.py nexgen_scada:/app/plc_driver.py
"""
    ssh.exec_command(cmd)
    
    # Restart the container
    ssh.exec_command('echo Raiz123 | sudo -S docker compose -f /home/raiz/SCADA_FINAL_1/docker-compose.yml restart scada_core')
    
    ssh.close()
except Exception as e:
    print(e)
