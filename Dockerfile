FROM ollama/ollama:latest

RUN sed -i 's|http://archive.ubuntu.com|https://archive.ubuntu.com|g; s|http://security.ubuntu.com|https://security.ubuntu.com|g' /etc/apt/sources.list.d/*.sources 2>/dev/null || \
    sed -i 's|http://archive.ubuntu.com|https://archive.ubuntu.com|g; s|http://security.ubuntu.com|https://security.ubuntu.com|g' /etc/apt/sources.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends python3 python3-pip curl && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip3 install --no-cache-dir --break-system-packages -r /app/requirements.txt

COPY src/ /app/
WORKDIR /app

# Start Ollama in background, pull configured models, then start the serverless handler
# OLLAMA_MODELS points to the RunPod network volume for model persistence
CMD bash -c "\
    echo '[startup] begin' && \
    export OLLAMA_MODELS=/runpod-volume/ollama && \
    echo \"[startup] OLLAMA_MODELS=${OLLAMA_MODELS}\" && \
    ollama serve >> /tmp/ollama.log 2>&1 & \
    echo '[startup] waiting for Ollama...' && \
    TIMEOUT=120; ELAPSED=0; \
    until curl -sf http://localhost:11434/api/tags > /dev/null 2>&1; do \
        sleep 2; ELAPSED=\$((ELAPSED+2)); \
        if [ \$ELAPSED -ge \$TIMEOUT ]; then \
            echo '[startup] ERROR: Ollama failed to start after 120s'; \
            cat /tmp/ollama.log; \
            exit 1; \
        fi; \
    done && \
    echo '[startup] Ollama ready' && \
    if [ -n \"${OLLAMA_CHAT_MODEL_NAME}\" ]; then echo \"[startup] pulling ${OLLAMA_CHAT_MODEL_NAME}\" && ollama pull \"${OLLAMA_CHAT_MODEL_NAME}\"; fi && \
    if [ -n \"${OLLAMA_EMBED_MODEL_NAME}\" ]; then echo \"[startup] pulling ${OLLAMA_EMBED_MODEL_NAME}\" && ollama pull \"${OLLAMA_EMBED_MODEL_NAME}\"; fi && \
    echo '[startup] starting handler' && \
    python3 handler.py"
