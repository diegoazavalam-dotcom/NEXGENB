import paramiko
import sys

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('192.168.100.211', username='raiz', password='Raiz123', timeout=10)
    
    ssh.exec_command('echo Raiz123 | sudo -S pkill -f snmp_covert_agent.py')
    ssh.exec_command('echo Raiz123 | sudo -S nohup /home/raiz/agent_venv/bin/python /home/raiz/snmp_covert_agent.py > /tmp/snmp_agent.log 2>&1 &')
    
    ssh.close()
    print("Agent restarted")
except Exception as e:
    print(e)
