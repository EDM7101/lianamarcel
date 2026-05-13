# syntax=docker/dockerfile:1
FROM nvidia/cuda:12.2.0-devel-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libssl-dev python3-pip python3-venv git pkg-config \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app/
ARG CCAP=86
ENV CUDA=/usr/local/cuda
RUN make -C /app/third_party/VanitySearch -j$(nproc) gpu=1 CCAP=${CCAP} CUDA=${CUDA}
RUN python3 -m venv /opt/venv && /opt/venv/bin/pip install --no-cache-dir -r /app/requirements.txt \
    && /opt/venv/bin/pip install --no-cache-dir -e /app

ENV PATH="/opt/venv/bin:${PATH}"
# Beim Start: config.yaml mounten, z. B.
# docker run --gpus all -v ./config.yaml:/etc/puzzle-lottery/config.yaml -v ./targets.txt:/opt/targets.txt puzzle-lottery \
#   puzzle-lottery -c /etc/puzzle-lottery/config.yaml
CMD ["puzzle-lottery", "-c", "/etc/puzzle-lottery/config.yaml"]
