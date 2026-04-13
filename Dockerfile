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
    export OLLAMA_MODELS=/runpod-volume/ollama && \
    ollama serve & \
    until curl -sf http://localhost:11434/api/tags > /dev/null 2>&1; do sleep 1; done && \
    if [ -n \"${OLLAMA_CHAT_MODEL_NAME}\" ]; then ollama pull \"${OLLAMA_CHAT_MODEL_NAME}\"; fi && \
    if [ -n \"${OLLAMA_EMBED_MODEL_NAME}\" ]; then ollama pull \"${OLLAMA_EMBED_MODEL_NAME}\"; fi && \
    python3 handler.py"
