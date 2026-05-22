import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    ssh.connect('192.168.100.48', username='raiz', password='Raiz123')
    
    # We will use sed to append pkg-config and libcairo2-dev to the apt-get install command in the Dockerfile
    cmd = "sed -i 's/build-essential/build-essential pkg-config libcairo2-dev/' /home/raiz/SCADA_FINAL_1/Dockerfile"
    stdin, stdout, stderr = ssh.exec_command(f'echo Raiz123 | sudo -S {cmd}')
    
    print("Dockerfile stdout:", stdout.read().decode())
    print("Dockerfile stderr:", stderr.read().decode())

    print("Rebuilding Docker...")
    # Rebuild again
    cmd_build = "cd ~/SCADA_FINAL_1 && echo Raiz123 | sudo -S docker compose up -d --build"
    stdin, stdout, stderr = ssh.exec_command(cmd_build)
    
    exit_status = stdout.channel.recv_exit_status()
    out = stdout.read().decode('utf-8', 'ignore')
    err = stderr.read().decode('utf-8', 'ignore')
    
    with open('C:\\SCADA_FINAL_1\\docker_out_2.txt', 'w', encoding='utf-8') as f:
        f.write(f"EXIT: {exit_status}\n")
        f.write("STDOUT:\n")
        f.write(out[-2000:])
        f.write("\nSTDERR:\n")
        f.write(err[-2000:])
        
except Exception as e:
    print(f"Exception: {e}")
finally:
    ssh.close()
