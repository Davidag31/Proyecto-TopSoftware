# Usa una imagen base de Python
FROM python:3.11-slim

# Instala las dependencias del sistema necesarias para mysqlclient y otras librerías
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Establece el directorio de trabajo en /app
WORKDIR /app

# Copia el archivo requirements.txt al contenedor
COPY requirements.txt .

# Instala las dependencias de Python
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copia el resto de los archivos de la aplicación al contenedor
COPY . .

# Expone el puerto que usará la aplicación Django
EXPOSE 8000

# Configura el punto de entrada para ejecutar el servidor de desarrollo de Django
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
