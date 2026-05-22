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
    
    print("Installing old pysnmp in venv to support asyncore...")
    run_ssh_command(ssh, '/home/raiz/agent_venv/bin/pip install pysnmp==4.4.12 pysmi==0.3.4')
    
    print("Restarting service...")
    run_ssh_command(ssh, 'echo Raiz123 | sudo -S systemctl restart snmp_agent.service')
    
    print("Checking service status...")
    status, out, err = run_ssh_command(ssh, 'echo Raiz123 | sudo -S journalctl -u snmp_agent.service -n 10 --no-pager')
    print(out.decode('utf-8', errors='ignore'))
    
except Exception as e:
    print(e)
finally:
    ssh.close()
