import paramiko
import sys
import time

def run_ssh_command(ssh, command):
    print(f"Running: {command}")
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    out = stdout.read().decode('utf-8')
    err = stderr.read().decode('utf-8')
    return exit_status, out, err

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print("Connecting to 192.168.100.211...")
    ssh.connect('192.168.100.211', username='raiz', password='Raiz123', timeout=10)
    print("Connected.")
    
    # 1. Start Docker service and enable it to start on boot
    print("Enabling and starting Docker service...")
    status, out, err = run_ssh_command(ssh, 'echo Raiz123 | sudo -S systemctl enable docker && echo Raiz123 | sudo -S systemctl start docker')
    print(f"Docker enable/start output: {out}\n{err}")

    # 2. Check if SCADA_FINAL_1 directory exists
    status, out, err = run_ssh_command(ssh, 'ls ~/SCADA_FINAL_1/docker-compose.yml')
    if status != 0:
        print("docker-compose.yml not found in ~/SCADA_FINAL_1. Attempting to locate...")
    else:
        print("Found docker-compose.yml.")

    # 3. Add restart: always to docker-compose.yml for the services to start on boot
    print("Updating docker-compose.yml to include restart: always...")
    sed_cmd = "echo Raiz123 | sudo -S sed -i '/image:/a \    restart: always' ~/SCADA_FINAL_1/docker-compose.yml"
    status, out, err = run_ssh_command(ssh, sed_cmd)
    
    # Also for build based services
    sed_cmd_2 = "echo Raiz123 | sudo -S sed -i '/build:/a \    restart: always' ~/SCADA_FINAL_1/docker-compose.yml"
    status, out, err = run_ssh_command(ssh, sed_cmd_2)
    print("Updated docker-compose.yml restart policies.")
    
    # Check what we updated
    status, out, err = run_ssh_command(ssh, 'cat ~/SCADA_FINAL_1/docker-compose.yml')
    print(f"docker-compose.yml content:\n{out}")

    # 4. Start the SCADA system
    print("Starting SCADA system with docker compose...")
    status, out, err = run_ssh_command(ssh, 'cd ~/SCADA_FINAL_1 && echo Raiz123 | sudo -S docker compose up -d')
    print(f"Docker compose output: {out}\n{err}")

    # 5. Check if it's running
    status, out, err = run_ssh_command(ssh, 'echo Raiz123 | sudo -S docker ps')
    print(f"Docker PS: \n{out}\n{err}")
    
except Exception as e:
    print(f"Error: {e}")
finally:
    ssh.close()
