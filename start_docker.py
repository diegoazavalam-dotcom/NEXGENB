import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    ssh.connect('192.168.100.48', username='raiz', password='Raiz123')
    
    stdin, stdout, stderr = ssh.exec_command('cd ~/SCADA_FINAL_1 && echo Raiz123 | sudo -S docker compose up -d --build')
    
    exit_status = stdout.channel.recv_exit_status()
    out = stdout.read().decode('utf-8', 'ignore')
    err = stderr.read().decode('utf-8', 'ignore')
    
    with open('C:\\SCADA_FINAL_1\\docker_out.txt', 'w', encoding='utf-8') as f:
        f.write(f"EXIT: {exit_status}\n")
        f.write("STDOUT:\n")
        f.write(out)
        f.write("\nSTDERR:\n")
        f.write(err)
        
except Exception as e:
    with open('C:\\SCADA_FINAL_1\\docker_out.txt', 'w', encoding='utf-8') as f:
        f.write(f"Exception: {e}")
finally:
    ssh.close()
