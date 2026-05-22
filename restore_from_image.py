import paramiko
import sys

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('192.168.100.211', username='raiz', password='Raiz123', timeout=10)
    
    # Run a temporary container and copy the original files out
    cmd = """echo Raiz123 | sudo -S bash -c "
    docker create --name temp_core scada_final_1-scada_core
    docker cp temp_core:/app/app.py /home/raiz/SCADA_FINAL_1/app.py
    docker cp temp_core:/app/sensor_gateway.py /home/raiz/SCADA_FINAL_1/sensor_gateway.py
    docker cp temp_core:/app/config_manager.py /home/raiz/SCADA_FINAL_1/config_manager.py
    docker rm temp_core
    "
    """
    stdin, stdout, stderr = ssh.exec_command(cmd)
    exit_status = stdout.channel.recv_exit_status()
    print("Exit status:", exit_status)
    sys.stdout.buffer.write(stdout.read())
    sys.stdout.buffer.write(stderr.read())
    
    print("Restarting docker container...")
    ssh.exec_command('cd ~/SCADA_FINAL_1 && echo Raiz123 | sudo -S docker compose restart scada_core')
    print("Done")
    
    ssh.close()
except Exception as e:
    print(e)
