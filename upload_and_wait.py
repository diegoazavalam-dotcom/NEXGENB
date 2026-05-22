import paramiko
import sys

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('192.168.100.211', username='raiz', password='Raiz123', timeout=10)
    
    sftp = ssh.open_sftp()
    sftp.put('C:\\SCADA_FINAL_1\\app.py.remote', '/tmp/app.py')
    sftp.close()
    
    print("Moving file and Restarting docker container...")
    stdin, stdout, stderr = ssh.exec_command('echo Raiz123 | sudo -S mv /tmp/app.py /home/raiz/SCADA_FINAL_1/app.py && cd /home/raiz/SCADA_FINAL_1 && echo Raiz123 | sudo -S docker compose restart scada_core')
    
    # We MUST wait for the command to finish by reading stdout and stderr!
    out = stdout.read()
    err = stderr.read()
    
    sys.stdout.buffer.write(out)
    sys.stdout.buffer.write(err)
    
    print("\nRestart finished!")
    ssh.close()
except Exception as e:
    print(e)
