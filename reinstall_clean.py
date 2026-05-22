import paramiko
import sys

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('192.168.100.211', username='raiz', password='Raiz123', timeout=10)
    
    # Install pysnmp and downgrade pyasn1
    cmd1 = 'echo Raiz123 | sudo -S docker exec -u 0 nexgen_scada pip install "pysnmp==4.4.12" "pysmi==0.3.4" pycryptodomex==3.23.0 "pyasn1==0.4.8"'
    ssh.exec_command(cmd1)
    
    # Restart to pick up the libraries
    ssh.exec_command('echo Raiz123 | sudo -S docker compose -f /home/raiz/SCADA_FINAL_1/docker-compose.yml restart scada_core')
    ssh.close()
except Exception as e:
    print(e)
