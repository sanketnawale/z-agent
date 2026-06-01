FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FASTAPI_URL=http://127.0.0.1:3001
ENV OLLAMA_URL=http://ollama:11434/api/generate
ENV ZOWE_REJECT_UNAUTHORIZED=false

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        ca-certificates \
        nodejs \
        npm \
    && rm -rf /var/lib/apt/lists/*

RUN npm install -g @zowe/cli

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY main.py /app/main.py
COPY ai_gateway.py /app/ai_gateway.py
COPY start.sh /app/start.sh
COPY jobfrontend /app/jobfrontend

RUN chmod +x /app/start.sh

EXPOSE 8001

CMD ["/app/start.sh"]
