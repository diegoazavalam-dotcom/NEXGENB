import paramiko
import sys

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('192.168.100.211', username='raiz', password='Raiz123', timeout=10)
    
    script = """
import os
for pid in os.listdir('/proc'):
    if pid.isdigit():
        try:
            with open(f'/proc/{pid}/cmdline', 'r') as f:
                cmd = f.read().replace('\\x00', ' ')
                if 'python' in cmd:
                    print(f'PID {pid}: {cmd}')
        except: pass
"""
    cmd = f"cat << 'EOF' > /tmp/check_procs_python.py\n{script}\nEOF\n"
    ssh.exec_command(cmd)
    ssh.exec_command('echo Raiz123 | sudo -S docker cp /tmp/check_procs_python.py nexgen_scada:/app/check_procs_python.py')
    
    stdin, stdout, stderr = ssh.exec_command('echo Raiz123 | sudo -S docker exec nexgen_scada python3 /app/check_procs_python.py')
    sys.stdout.buffer.write(stdout.read())
    ssh.close()
except Exception as e:
    print(e)
