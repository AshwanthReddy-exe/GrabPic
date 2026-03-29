FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    gcc \
    g++ \
    python3-dev \
    ffmpeg \
    libsm6 \
    libxext6 \
    wget \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# 🔥 Download and FIX model structure
RUN mkdir -p /root/.insightface/models/buffalo_l && \
    wget https://github.com/deepinsight/insightface/releases/download/v0.7/buffalo_l.zip -O /tmp/model.zip && \
    unzip /tmp/model.zip -d /tmp && \
    mv /tmp/*.onnx /root/.insightface/models/buffalo_l/ && \
    rm -rf /tmp/model.zip /tmp/*.onnx

COPY requirements.txt .

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    apt-get purge -y build-essential gcc g++ python3-dev && \
    apt-get autoremove -y && \
    rm -rf /root/.cache/pip

COPY . .

ENV BASE_DATA_DIR=/app/data
ENV QUERY_DIR=/app/query_data
ENV PYTHONPATH=/app

RUN mkdir -p /app/data/events /app/query_data

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
