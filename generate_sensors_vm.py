import paramiko
import sys

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('192.168.100.211', username='raiz', password='Raiz123', timeout=10)
    
    script = """
import database
import time

sensores = []

# 4 Honeywell XCD (Gas Sensors) - 4-20mA or S7 REAL values
for i in range(1, 5):
    sensores.append({
        'n': f'Gas_Honeywell_{i}',
        'id': '192.168.0.10',
        'protocolo': 'S7',
        'm': 'REAL',
        'u': '% LEL',
        'db': 100,
        'off': float(i * 4), # e.g. 4.0, 8.0, 12.0, 16.0
        'la': 20.0,
        'lb': 0.0,
        'lh': 100.0
    })

# 8 Extractores (Motores) - BOOL values
for i in range(1, 9):
    sensores.append({
        'n': f'Extractor_{i}',
        'id': '192.168.0.10',
        'protocolo': 'S7',
        'm': 'BOOL',
        'u': 'ESTADO',
        'db': 100,
        'off': float(20 + (i * 0.1)), # e.g. 20.1, 20.2...
        'la': 1.0,
        'lb': 0.0,
        'lh': 1.0
    })

for s in sensores:
    print(f"Registrando {s['n']}...")
    database.registrar_nuevo_sensor_completo(s)

print("¡12 Sensores generados con éxito!")
"""
    cmd = f"cat << 'EOF' > /tmp/generate_sensors.py\n{script}\nEOF\n"
    ssh.exec_command(cmd)
    
    ssh.exec_command('echo Raiz123 | sudo -S docker cp /tmp/generate_sensors.py nexgen_scada:/app/generate_sensors.py')
    
    stdin, stdout, stderr = ssh.exec_command('echo Raiz123 | sudo -S docker exec nexgen_scada python3 /app/generate_sensors.py')
    sys.stdout.buffer.write(stdout.read())
    sys.stdout.buffer.write(stderr.read())
    ssh.close()
except Exception as e:
    print(e)
