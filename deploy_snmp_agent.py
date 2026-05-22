import paramiko
from scp import SCPClient

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
    print("Connecting to VM...")
    ssh.connect('192.168.100.211', username='raiz', password='Raiz123', timeout=10)
    
    print("Uploading snmp_covert_agent.py...")
    with SCPClient(ssh.get_transport()) as scp:
        scp.put(r'C:\SCADA_FINAL_1\snmp_covert_agent.py', '/home/raiz/snmp_covert_agent.py')
        
    print("Installing dependencies...")
    status, out, err = run_ssh_command(ssh, 'echo Raiz123 | sudo -S apt update && echo Raiz123 | sudo -S apt install -y python3-psutil python3-pip')
    print(out, err)
    
    # We will install pysnmp using pip to ensure we get the right version
    status, out, err = run_ssh_command(ssh, 'echo Raiz123 | sudo -S pip3 install pysnmp --break-system-packages')
    print(out, err)
    
    print("Creating systemd service...")
    service_content = """[Unit]
Description=SNMP Covert Agent
After=network.target

[Service]
Type=simple
User=root
ExecStart=/usr/bin/python3 /home/raiz/snmp_covert_agent.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
"""
    # Write to tmp first then copy
    cmd = f"cat << 'EOF' > /tmp/snmp_agent.service\n{service_content}EOF\n"
    run_ssh_command(ssh, cmd)
    
    run_ssh_command(ssh, 'echo Raiz123 | sudo -S mv /tmp/snmp_agent.service /etc/systemd/system/snmp_agent.service')
    
    print("Enabling and starting service...")
    run_ssh_command(ssh, 'echo Raiz123 | sudo -S systemctl daemon-reload')
    run_ssh_command(ssh, 'echo Raiz123 | sudo -S systemctl enable snmp_agent.service')
    run_ssh_command(ssh, 'echo Raiz123 | sudo -S systemctl start snmp_agent.service')
    
    print("Checking service status...")
    status, out, err = run_ssh_command(ssh, 'echo Raiz123 | sudo -S systemctl status snmp_agent.service')
    print(out)
    
except Exception as e:
    print(e)
finally:
    ssh.close()
