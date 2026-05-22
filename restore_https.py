import paramiko

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('192.168.100.211', username='raiz', password='Raiz123', timeout=10)
    
    # Re-add ssl_context='adhoc'
    sed_cmd = "echo Raiz123 | sudo -S sed -i \"s/app.run(debug=False, host='0.0.0.0', port=5005, use_reloader=False)/app.run(debug=False, host='0.0.0.0', port=5005, use_reloader=False, ssl_context='adhoc')/\" /home/raiz/SCADA_FINAL_1/app.py"
    ssh.exec_command(sed_cmd)
    
    print("Restarting docker container...")
    stdin, stdout, stderr = ssh.exec_command('cd ~/SCADA_FINAL_1 && echo Raiz123 | sudo -S docker compose restart scada_core')
    exit_status = stdout.channel.recv_exit_status()
    print("Exit status:", exit_status)
    ssh.close()
    print("Done")
except Exception as e:
    print(e)
