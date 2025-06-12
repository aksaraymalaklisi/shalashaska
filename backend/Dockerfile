# Stage 1: Build environment and dependencies
FROM condaforge/miniforge3:latest AS builder

WORKDIR /usr/src/app

RUN apt-get update && apt-get install -y \
    build-essential \
    gdal-bin \
    libgdal-dev \
    libproj-dev \
    && rm -rf /var/lib/apt/lists/*

COPY environment.yml .
RUN conda env create -f environment.yml

COPY . .

RUN /bin/bash -c "source activate shalashaska && pip install gunicorn"

# Stage 2: Distroless runtime
FROM gcr.io/distroless/base-debian12

WORKDIR /usr/src/app

# Copie o ambiente conda pronto
COPY --from=builder /opt/conda/envs/shalashaska /opt/conda/envs/shalashaska
COPY --from=builder /usr/src/app /usr/src/app

ENV PATH="/opt/conda/envs/shalashaska/bin:$PATH"
ENV PYTHONUNBUFFERED=1

EXPOSE 7777

CMD ["gunicorn", "queequeg.wsgi:application", "--bind", "0.0.0.0:7777"]