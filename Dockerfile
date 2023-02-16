# Author: Markel Elorza
# Version: 0.1
# Description: Containerize terraform state manager app

FROM python:3.9-alpine

# Instalar Git
RUN apk update && apk add git

# Descargar y descomprimir Terraform
RUN wget https://releases.hashicorp.com/terraform/1.3.8/terraform_1.3.8_linux_amd64.zip && \
    unzip terraform_1.3.8_linux_amd64.zip && \
    mv terraform /usr/local/bin/

# Copiar el código Python al contenedor
COPY main.py /app/main.py

# Instalar las dependencias de Python
COPY requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

# Establecer la ubicación de trabajo como el directorio de la aplicación
WORKDIR /app

# Ejecutar el script Python al iniciar el contenedor
CMD ["sleep", "99d"]

