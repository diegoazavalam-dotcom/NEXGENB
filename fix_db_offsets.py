import paramiko
import sys

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('192.168.100.211', username='raiz', password='Raiz123', timeout=10)
    
    script = """
import database
conn = database.get_db_connection()
cur = conn.cursor()
cur.execute("UPDATE configuracion_sensores SET offset_val=1.0 WHERE nombre_sensor='Linux_CPU_Usage'")
cur.execute("UPDATE configuracion_sensores SET offset_val=2.0 WHERE nombre_sensor='Linux_RAM_Usage'")
cur.execute("UPDATE configuracion_sensores SET offset_val=3.0 WHERE nombre_sensor='Linux_Disk_Usage'")
conn.commit()
"""
    cmd = f"cat << 'EOF' > /tmp/fix_offsets.py\n{script}\nEOF\n"
    ssh.exec_command(cmd)
    ssh.exec_command('echo Raiz123 | sudo -S docker cp /tmp/fix_offsets.py nexgen_scada:/app/fix_offsets.py')
    
    stdin, stdout, stderr = ssh.exec_command('echo Raiz123 | sudo -S docker exec nexgen_scada python3 /app/fix_offsets.py')
    sys.stdout.buffer.write(stdout.read())
    
    # Reload gateway
    reload_cmd = "import urllib.request; req=urllib.request.Request('http://127.0.0.1:5006/reload_config', method='POST'); print(urllib.request.urlopen(req).read().decode())"
    stdin, stdout, stderr = ssh.exec_command(f'echo Raiz123 | sudo -S docker exec nexgen_scada python3 -c "{reload_cmd}"')
    sys.stdout.buffer.write(stdout.read())
    
    ssh.close()
except Exception as e:
    print(e)
