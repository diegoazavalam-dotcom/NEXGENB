import paramiko
import sys

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
    
    # Try installing from apt just in case
    print("Installing python3-pysnmp4 via apt...")
    status, out, err = run_ssh_command(ssh, 'echo Raiz123 | sudo -S apt install -y python3-pysnmp4')
    
    # Also just plain pip3 install if not found in apt
    print("Installing pysnmp via pip...")
    status, out, err = run_ssh_command(ssh, 'echo Raiz123 | sudo -S pip3 install pysnmp')
    
    print("Restarting service...")
    run_ssh_command(ssh, 'echo Raiz123 | sudo -S systemctl restart snmp_agent.service')
    
    print("Checking service status...")
    status, out, err = run_ssh_command(ssh, 'echo Raiz123 | sudo -S journalctl -u snmp_agent.service -n 20 --no-pager')
    print(out.decode('utf-8', errors='ignore'))
    
except Exception as e:
    print(e)
finally:
    ssh.close()
