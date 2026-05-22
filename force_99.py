import paramiko
import sys

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('192.168.100.211', username='raiz', password='Raiz123', timeout=10)
    
    cmd = "echo Raiz123 | sudo -S sed -i 's/return 0.0/return 99.9/' /home/raiz/SCADA_FINAL_1/plc_driver.py"
    ssh.exec_command(cmd)
    
    # Also I will remove the __pycache__ volume completely
    ssh.exec_command('echo Raiz123 | sudo -S docker compose -f /home/raiz/SCADA_FINAL_1/docker-compose.yml down -v')
    
    # I MUST reinstall pysnmp since I destroyed the venv volume too (wait! /app/venv is an anonymous volume! If I destroy it, pip dependencies are LOST! But they were installed in /usr/local/lib/python3.11/site-packages!)
    ssh.exec_command('echo Raiz123 | sudo -S docker compose -f /home/raiz/SCADA_FINAL_1/docker-compose.yml up -d')
    
    ssh.close()
except Exception as e:
    print(e)
