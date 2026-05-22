import paramiko
from scp import SCPClient

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    ssh.connect('192.168.100.48', username='raiz', password='Raiz123')
    
    with SCPClient(ssh.get_transport()) as scp:
        scp.put('c:\\Users\\betoo\\Downloads\\SCADA_FINAL_1-20260422T040553Z-3-001\\SCADA_FINAL_1\\startup_wizard.py', '/home/raiz/SCADA_FINAL_1/startup_wizard.py')
    
    # Restart the container
    stdin, stdout, stderr = ssh.exec_command('echo Raiz123 | sudo -S docker restart nexgen_scada')
    print("Restart STDOUT:", stdout.read().decode())
    print("Restart STDERR:", stderr.read().decode())

except Exception as e:
    print(e)
finally:
    ssh.close()
