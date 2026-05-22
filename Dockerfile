FROM python:3.11-slim

# Instalar dependencias del sistema operativo (necesarias para psycopg2, snap7, etc)
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    python3-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar requirements y dependencias
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt
# Instalar gunicorn y supervisor si se necesitan, pero usaremos bash script por simplicidad
RUN pip install --no-cache-dir gunicorn

# Copiar el código fuente
COPY . .

# Dar permisos de ejecución al script de arranque
RUN chmod +x start.sh

# Exponer puertos HMI (5005) y Gateway (5006)
EXPOSE 5005 5006

# Comando de inicio
CMD ["./start.sh"]
