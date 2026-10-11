FROM python:3.12-slim

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install latest yt-dlp
RUN curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -o /usr/local/bin/yt-dlp \
    && chmod a+rx /usr/local/bin/yt-dlp

# Install wireproxy (userspace WireGuard → SOCKS5)
RUN curl -L https://github.com/windtf/wireproxy/releases/latest/download/wireproxy_linux_amd64.tar.gz \
    | tar xz -C /usr/local/bin wireproxy \
    && chmod +x /usr/local/bin/wireproxy

WORKDIR /app

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App files
COPY main.py .
COPY wireproxy.conf .

# Expose port (Render uses PORT env, default 10000)
ENV PORT=10000

# Start wireproxy in background then the API
CMD ["sh", "-c", "wireproxy -c /app/wireproxy.conf & sleep 3 && uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
