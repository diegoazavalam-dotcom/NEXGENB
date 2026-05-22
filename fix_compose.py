import paramiko

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('192.168.100.211', username='raiz', password='Raiz123', timeout=10)
    
    # We inject GOD_MODE_TOKEN to docker-compose.yml
    remote_script = """
import yaml

with open('/home/raiz/SCADA_FINAL_1/docker-compose.yml', 'r') as f:
    config = yaml.safe_load(f)

config['services']['scada_core']['environment'].append('GOD_MODE_TOKEN=LeoyZoe0822')

with open('/home/raiz/SCADA_FINAL_1/docker-compose.yml', 'w') as f:
    yaml.dump(config, f, default_flow_style=False)
"""
    cmd = f"cat << 'EOF' > /tmp/fix_compose.py\n{remote_script}\nEOF\n"
    ssh.exec_command(cmd)
    
    stdin, stdout, stderr = ssh.exec_command('echo Raiz123 | sudo -S pip3 install pyyaml && python3 /tmp/fix_compose.py')
    print(stdout.read().decode('utf-8'))
    print(stderr.read().decode('utf-8'))
    
    print("Restarting docker container...")
    ssh.exec_command('cd ~/SCADA_FINAL_1 && echo Raiz123 | sudo -S docker compose up -d')
    print("Done")
    
    ssh.close()
except Exception as e:
    print(e)
