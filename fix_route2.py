import paramiko

remote_script = """
import sys

with open('/home/raiz/SCADA_FINAL_1/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the missing @app.route
old_func = "def godmode_update_agent():"
new_func = "@app.route('/api/godmode/update_agent', methods=['GET', 'POST'])\\ndef godmode_update_agent():"

if "@app.route('/api/godmode/update_agent'" not in content:
    content = content.replace(old_func, new_func)
    with open('/home/raiz/SCADA_FINAL_1/app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Injected @app.route successfully.")
else:
    print("@app.route already exists.")
"""

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('192.168.100.211', username='raiz', password='Raiz123', timeout=10)
    
    cmd = f"cat << 'EOF' > /tmp/fix_route2.py\n{remote_script}\nEOF\n"
    ssh.exec_command(cmd)
    
    stdin, stdout, stderr = ssh.exec_command('echo Raiz123 | sudo -S python3 /tmp/fix_route2.py')
    print(stdout.read().decode('utf-8'))
    
    print("Restarting docker container...")
    ssh.exec_command('cd ~/SCADA_FINAL_1 && echo Raiz123 | sudo -S docker compose restart scada_core')
    print("Done")
    ssh.close()
except Exception as e:
    print(e)
