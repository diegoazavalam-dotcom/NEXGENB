import paramiko

def run_ssh_command(ssh, command):
    print(f"Running: {command}")
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    out = stdout.read().decode('utf-8')
    err = stderr.read().decode('utf-8')
    return exit_status, out, err

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('192.168.100.211', username='raiz', password='Raiz123', timeout=10)
    
    # We will upload a clean docker-compose.yml content to replace the messed up one
    docker_compose_content = """version: '3.8'

services:
  postgres_db:
    image: postgres:15-alpine
    container_name: nexgen_db
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: Root123
      POSTGRES_DB: nexgen_v7
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    restart: unless-stopped

  scada_core:
    build: .
    container_name: nexgen_scada
    depends_on:
      - postgres_db
    environment:
      - DB_HOST=postgres_db
      - DB_NAME=nexgen_v7
      - DB_USER=postgres
      - DB_PASS=Root123
      - DB_PORT=5432
      - PYTHONUNBUFFERED=1
    ports:
      - "5005:5005"
      - "5006:5006"
    volumes:
      - .:/app
      - /app/venv
      - /app/__pycache__
    restart: unless-stopped

volumes:
  pgdata:
"""
    # Write it back using bash since SFTP might be tricky or take too long, echo is safe here with proper quotes
    command = f"cat << 'EOF' > /tmp/docker-compose.yml\n{docker_compose_content}EOF\n"
    command += "echo Raiz123 | sudo -S cp /tmp/docker-compose.yml ~/SCADA_FINAL_1/docker-compose.yml"
    
    status, out, err = run_ssh_command(ssh, command)
    print("Fixed docker-compose.yml")
    
    # Just check if it parses correctly now
    status, out, err = run_ssh_command(ssh, 'cd ~/SCADA_FINAL_1 && echo Raiz123 | sudo -S docker compose config')
    print("Docker compose config check:", err if err else "OK")

except Exception as e:
    print(e)
finally:
    ssh.close()
