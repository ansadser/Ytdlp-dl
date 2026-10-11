# ---------- Stage 1: bgutil PO token server (Node) ----------
FROM node:20-slim AS pot
RUN apt-get update && apt-get install -y --no-install-recommends git ca-certificates \
    && rm -rf /var/lib/apt/lists/*
RUN git clone --depth 1 https://github.com/Brainicism/bgutil-ytdlp-pot-provider.git /pot
WORKDIR /pot/server
RUN npm ci && npx tsc

# ---------- Stage 2: API ----------
FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# node binary + built PO token server
COPY --from=pot /usr/local/bin/node /usr/local/bin/node
COPY --from=pot /pot/server /pot/server

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY main.py .

ENV PORT=10000
EXPOSE 10000

# start: PO token server (port 4416) in background, update yt-dlp, then the API
CMD ["sh", "-c", "node /pot/server/build/main.js & (pip install -U --no-cache-dir 'yt-dlp[default]' >/dev/null 2>&1 || true); exec uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
