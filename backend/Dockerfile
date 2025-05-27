# Use imagem base com OSMnx e Conda já instalados (Python 3.13)
FROM ghcr.io/osmnx/osmnx:latest

# Diretório de trabalho
WORKDIR /app

# Copia o requirements.txt do ambiente (Conda)
COPY requirements.txt /tmp/requirements.txt

# Cria o ambiente Conda e ativa
RUN conda create -n pequod --file /tmp/requirements.txt python=3.13 && \
    conda clean -afy

# Copia o backend para o contêiner
COPY backend/ /app/

# Ativa o ambiente e instala Gunicorn (caso não esteja no requirements)
RUN /bin/bash -c "source /opt/conda/etc/profile.d/conda.sh && conda activate pequod && pip install gunicorn"

# Expõe a porta padrão do Gunicorn
EXPOSE 8000

# Define variáveis de ambiente para o Django
ENV DJANGO_SETTINGS_MODULE=queequeg.settings
ENV PYTHONUNBUFFERED=1

# Entrypoint: ativa o ambiente Conda e executa o Gunicorn
ENTRYPOINT ["/bin/bash", "-c", "source /opt/conda/etc/profile.d/conda.sh && conda activate pequod && gunicorn queequeg.wsgi:application --bind 0.0.0.0:8000"]