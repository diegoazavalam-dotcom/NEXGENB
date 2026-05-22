import paramiko
import sys

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('192.168.100.211', username='raiz', password='Raiz123', timeout=10)
    
    # We will just write a wrapper script
    wrapper = """#!/bin/bash
/home/raiz/agent_venv/bin/python /home/raiz/snmp_covert_agent.py > /tmp/snmp_agent.log 2>&1 &
"""
    cmd = f"cat << 'EOF' > /tmp/run_agent.sh\n{wrapper}\nEOF\nchmod +x /tmp/run_agent.sh"
    ssh.exec_command(cmd)
    
    ssh.exec_command('echo Raiz123 | sudo -S /tmp/run_agent.sh')
    ssh.close()
    print("Agent started")
except Exception as e:
    print(e)
