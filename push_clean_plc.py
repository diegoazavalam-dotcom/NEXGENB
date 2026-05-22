import paramiko
import sys

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('192.168.100.211', username='raiz', password='Raiz123', timeout=10)
    
    with open('C:\\SCADA_FINAL_1\\clean_plc_driver.py', 'r') as f:
        content = f.read()

    # Write the clean content to the host VM
    script = "cat << 'EOF' > /home/raiz/SCADA_FINAL_1/plc_driver.py\n" + content + "\nEOF\n"
    ssh.exec_command(script)
    
    # Restart the gateway service gracefully
    ssh.exec_command('echo Raiz123 | sudo -S docker compose -f /home/raiz/SCADA_FINAL_1/docker-compose.yml restart scada_core')
    
    ssh.close()
    print("Fixed plc driver")
except Exception as e:
    print(e)
