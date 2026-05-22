import paramiko
import sys

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('192.168.100.211', username='raiz', password='Raiz123', timeout=10)
    
    with open('C:\\SCADA_FINAL_1\\clean_plc_driver.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # Create a wrapper script on the VM that writes the file to avoid bash escaping issues
    script = "cat << 'EOF' > /home/raiz/SCADA_FINAL_1/plc_driver.py\n" + content + "\nEOF\n"
    
    stdin, stdout, stderr = ssh.exec_command(script)
    stdout.read()
    
    # Restart the gateway service gracefully
    ssh.exec_command('echo Raiz123 | sudo -S docker compose -f /home/raiz/SCADA_FINAL_1/docker-compose.yml restart scada_core')
    
    ssh.close()
    print("Fixed plc driver properly")
except Exception as e:
    print(e)
