import os
import sys
import paramiko
from scp import SCPClient

def progress(filename, size, sent):
    sys.stdout.write(f"\rCopiando {filename} ... {float(sent)/float(size)*100:.2f}%")
    sys.stdout.flush()

def run_command(ssh, cmd):
    if "sudo" in cmd:
        cmd = cmd.replace("sudo ", "sudo -S ")
        
    print(f"\n[Ejecutando en VM]: {cmd}")
    stdin, stdout, stderr = ssh.exec_command(cmd)
    
    # Si el comando requiere sudo, pasamos la contraseña
    if "sudo" in cmd:
        stdin.write("Raiz123\n")
        stdin.flush()
        
    for line in stdout:
        print(line.strip())
    for line in stderr:
        print(f"ERROR: {line.strip()}")
    
    return stdout.channel.recv_exit_status()

def main():
    host = "192.168.100.48"
    user = "raiz"
    password = "Raiz123"
    
    print(f"Conectando a {host}...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(host, username=user, password=password, timeout=10)
    except Exception as e:
        print(f"Error conectando a SSH: {e}")
        return

    print("Conexión SSH exitosa.")
    
    # Crear directorio si no existe
    run_command(ssh, "mkdir -p ~/SCADA_FINAL_1")
    
    # 2. Instalar Docker si no está instalado
    print("\nVerificando instalación de Docker...")
    status = run_command(ssh, "docker --version")
    if status != 0:
        print("Docker no encontrado. Instalando Docker (esto puede tardar un poco)...")
        run_command(ssh, "curl -fsSL https://get.docker.com -o get-docker.sh")
        run_command(ssh, "sudo sh get-docker.sh")
        run_command(ssh, "sudo systemctl start docker")
        run_command(ssh, "sudo systemctl enable docker")
        run_command(ssh, f"sudo usermod -aG docker {user}")
    
    status_compose = run_command(ssh, "docker compose version")
    if status_compose != 0:
        run_command(ssh, "docker-compose --version")
        
    # Limpiar procesos viejos
    print("\nDeteniendo contenedores viejos (si existen)...")
    run_command(ssh, "cd ~/SCADA_FINAL_1 && sudo docker compose down || sudo docker-compose down")
    run_command(ssh, "sudo rm -rf ~/SCADA_FINAL_1/*")

    # Transferir archivos por SCP
    print("\nIniciando transferencia de archivos (SCP)...")
    local_path = "C:\\SCADA_FINAL_1"
    remote_path = "/home/raiz/SCADA_FINAL_1/"
    
    # Evitar copiar venv, __pycache__, .git, base de datos local pesada
    archivos_ignorar = ['.git', 'venv', '__pycache__', 'nexgen_scada.db', '.env', 'dist', 'build', 'NexGen_SCADA_V7_Installer', 'dist_old', 'NexGen_SCADA_V7_Installer.zip']
    
    with SCPClient(ssh.get_transport(), progress=progress) as scp:
        for item in os.listdir(local_path):
            if item in archivos_ignorar:
                continue
            item_path = os.path.join(local_path, item)
            try:
                if os.path.isdir(item_path):
                    scp.put(item_path, recursive=True, remote_path=remote_path)
                else:
                    scp.put(item_path, remote_path=remote_path)
            except Exception as e:
                print(f"\nAdvertencia: No se pudo copiar {item} - {e}")
    
    print("\nTransferencia completada.")
    
    # Asegurarnos de que start.sh es ejecutable
    run_command(ssh, "sudo chmod +x ~/SCADA_FINAL_1/start.sh")
    
    # Iniciar Docker Compose
    print("\nLevantando contenedores Docker...")
    run_command(ssh, "cd ~/SCADA_FINAL_1 && sudo docker compose up -d --build || sudo docker-compose up -d --build")
    
    print("\nDespliegue finalizado.")
    
    ssh.close()

if __name__ == "__main__":
    main()
