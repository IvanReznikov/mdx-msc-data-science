FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# Unbuffered stdout so every log line reaches the host (Render Logs) instantly -
# buffered output hides crash tracebacks when the process dies.
ENV PYTHONUNBUFFERED=1
# Render injects PORT (free plan expects the container to bind it);
# other hosts (e.g. a HF Space with app_port: 7860) fall back to 7860.
CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT:-7860}"]
