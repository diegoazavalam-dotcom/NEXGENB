import paramiko

def run_ssh_command(ssh, command):
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    out = stdout.read()
    err = stderr.read()
    return exit_status, out, err

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('192.168.100.211', username='raiz', password='Raiz123', timeout=10)
    
    print("Creating virtualenv for the agent...")
    run_ssh_command(ssh, 'echo Raiz123 | sudo -S apt install -y python3-venv')
    run_ssh_command(ssh, 'mkdir -p /home/raiz/agent_venv && python3 -m venv /home/raiz/agent_venv')
    
    print("Installing dependencies in venv...")
    run_ssh_command(ssh, '/home/raiz/agent_venv/bin/pip install psutil pysnmp pysmi')
    
    print("Updating systemd service...")
    service_content = """[Unit]
Description=SNMP Covert Agent
After=network.target

[Service]
Type=simple
User=root
ExecStart=/home/raiz/agent_venv/bin/python /home/raiz/snmp_covert_agent.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
"""
    cmd = f"cat << 'EOF' > /tmp/snmp_agent.service\n{service_content}EOF\n"
    run_ssh_command(ssh, cmd)
    run_ssh_command(ssh, 'echo Raiz123 | sudo -S mv /tmp/snmp_agent.service /etc/systemd/system/snmp_agent.service')
    
    print("Restarting service...")
    run_ssh_command(ssh, 'echo Raiz123 | sudo -S systemctl daemon-reload')
    run_ssh_command(ssh, 'echo Raiz123 | sudo -S systemctl restart snmp_agent.service')
    
    print("Checking service status...")
    status, out, err = run_ssh_command(ssh, 'echo Raiz123 | sudo -S journalctl -u snmp_agent.service -n 10 --no-pager')
    print(out.decode('utf-8', errors='ignore'))
    
except Exception as e:
    print(e)
finally:
    ssh.close()
