# Dockerfile para ReporteCOG (Raspberry Pi)
FROM python:3.11-slim

# Evitar prompts de paquetes
ENV DEBIAN_FRONTEND=noninteractive

# Instalar dependencias de sistema (LaTeX y herramientas)
RUN apt-get update && apt-get install -y \
    texlive-latex-base \
    texlive-latex-extra \
    texlive-fonts-recommended \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de trabajo
WORKDIR /app

# Copiar requerimientos e instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código
COPY . .

# Asegurar que existan las carpetas de persistencia
RUN mkdir -p outputs

# Exponer el puerto de Streamlit
EXPOSE 8501

# Comando para ejecutar la app
CMD ["streamlit", "run", "run.py", "--server.port=8501", "--server.address=0.0.0.0"]
