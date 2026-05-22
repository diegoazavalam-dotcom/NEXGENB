import paramiko
import sys

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('192.168.100.211', username='raiz', password='Raiz123', timeout=10)
    
    script = """
import database

sensores = [
    {"n": "Linux_CPU_Usage", "id": "192.168.100.211:161", "protocolo": "SNMP", "m": "REAL", "u": "%", "la": 80.0, "lb": 10.0, "off": 0.0, "db": 0},
    {"n": "Linux_RAM_Usage", "id": "192.168.100.211:161", "protocolo": "SNMP", "m": "REAL", "u": "%", "la": 85.0, "lb": 10.0, "off": 0.0, "db": 0},
    {"n": "Linux_Disk_Usage", "id": "192.168.100.211:161", "protocolo": "SNMP", "m": "REAL", "u": "%", "la": 90.0, "lb": 10.0, "off": 0.0, "db": 0}
]

for s in sensores:
    success = database.registrar_nuevo_sensor_completo(s)
    print(f"Sensor {s['n']} registered: {success}")
"""
    cmd = f"cat << 'EOF' > /tmp/create_sensors.py\n{script}\nEOF\n"
    ssh.exec_command(cmd)
    
    stdin, stdout, stderr = ssh.exec_command('echo Raiz123 | sudo -S docker exec nexgen_scada python3 /tmp/create_sensors.py')
    out = stdout.read()
    sys.stdout.buffer.write(out)
    ssh.close()
except Exception as e:
    print(e)
