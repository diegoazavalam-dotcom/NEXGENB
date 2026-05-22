import threading
import requests
import time
import sys

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

URL_AUTH = "https://127.0.0.1:5005/api/auth/login"
URL_TELEMETRY = "https://127.0.0.1:5005/api/telemetria"
URL_STATUS = "https://127.0.0.1:5005/api/plc/status"

# Parámetros de la prueba
NUM_USERS = 50
REQUESTS_PER_USER = 20

# Estadísticas
success_count = 0
error_count = 0
latencies = []
lock = threading.Lock()

def simulate_user(user_id):
    global success_count, error_count, latencies
    session = requests.Session()
    
    # 1. Login
    try:
        res = session.post(URL_AUTH, json={"username": "admin", "password": "1234"}, timeout=5, verify=False)
        if res.status_code != 200:
            with lock: error_count += REQUESTS_PER_USER
            return
    except:
        with lock: error_count += REQUESTS_PER_USER
        return

    # 2. Hacer peticiones concurrentes
    for i in range(REQUESTS_PER_USER):
        try:
            start_time = time.time()
            # Intercalamos peticiones de telemetría y status
            if i % 2 == 0:
                r = session.get(URL_TELEMETRY, timeout=5, verify=False)
            else:
                r = session.get(URL_STATUS, timeout=5, verify=False)
                
            latency = (time.time() - start_time) * 1000 # ms
            
            with lock:
                if r.status_code == 200:
                    success_count += 1
                    latencies.append(latency)
                else:
                    error_count += 1
        except Exception as e:
            with lock:
                error_count += 1
        
        # Pequeña pausa realista
        time.sleep(0.05)

def run_stress_test():
    print(f"🚀 Iniciando Stress Test: {NUM_USERS} Usuarios Concurrentes x {REQUESTS_PER_USER} Peticiones...")
    start_global = time.time()
    threads = []
    
    for i in range(NUM_USERS):
        t = threading.Thread(target=simulate_user, args=(i,))
        threads.append(t)
        t.start()
        
    for t in threads:
        t.join()
        
    total_time = time.time() - start_global
    
    print("\n📊 RESULTADOS DE LA PRUEBA DE STRESS 📊")
    print(f"Tiempo Total: {total_time:.2f} segundos")
    print(f"Peticiones Exitosas: {success_count}")
    print(f"Peticiones Fallidas: {error_count}")
    if success_count > 0:
        avg_latency = sum(latencies) / len(latencies)
        max_latency = max(latencies)
        min_latency = min(latencies)
        print(f"Latencia Promedio: {avg_latency:.2f} ms")
        print(f"Latencia Mínima: {min_latency:.2f} ms")
        print(f"Latencia Máxima: {max_latency:.2f} ms")
        print(f"Rendimiento: {success_count / total_time:.2f} req/sec")

if __name__ == '__main__':
    run_stress_test()
