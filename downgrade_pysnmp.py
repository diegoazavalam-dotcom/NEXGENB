import paramiko
import sys

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('192.168.100.211', username='raiz', password='Raiz123', timeout=10)
    
    stdin, stdout, stderr = ssh.exec_command('echo Raiz123 | sudo -S docker exec -u 0 nexgen_scada pip install "pysnmp==4.4.12" "pysmi==0.3.4" --force-reinstall')
    sys.stdout.buffer.write(stdout.read())
    sys.stdout.buffer.write(stderr.read())
    
    # Check if the import now works
    stdin, stdout, stderr = ssh.exec_command('echo Raiz123 | sudo -S docker exec nexgen_scada python3 -c "from pysnmp.hlapi import getCmd; print(\'OK hlapi\')"')
    sys.stdout.buffer.write(stdout.read())
    
    # Restart container
    ssh.exec_command('echo Raiz123 | sudo -S docker compose -f /home/raiz/SCADA_FINAL_1/docker-compose.yml restart scada_core')
    
    ssh.close()
except Exception as e:
    print(e)
