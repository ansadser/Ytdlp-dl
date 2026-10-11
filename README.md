# yt-dlp + Cloudflare WARP API

Fast & free YouTube (and 1800+ sites) direct stream URL extractor.  
Uses **yt-dlp** + **Cloudflare WARP** (via wireproxy) so Render/Railway datacenter IPs don't get blocked.

## Features

- Extremely fast (only extracts direct CDN URLs, no full download on server)
- Handles large files (4K etc.) because client downloads directly
- Free Cloudflare WARP exit IP
- Simple REST API
- Ready for Render free tier

## Quick Start

### 1. Generate your own WARP config (do this once on your PC)

```bash
# Download wgcf
wget https://github.com/ViRb3/wgcf/releases/latest/download/wgcf_2.2.26_linux_amd64 -O wgcf
chmod +x wgcf

# Register free Cloudflare WARP account
./wgcf register

# Generate WireGuard profile
./wgcf generate
```

This creates `wgcf-profile.conf`. Open it and copy the `PrivateKey = ...` line.

### 2. Create your wireproxy.conf

```bash
cp wireproxy.conf.example wireproxy.conf
```

Open `wireproxy.conf` and replace `YOUR_PRIVATE_KEY_HERE` with the PrivateKey you got from wgcf.

### 3. Deploy to Render

1. Push this repo to GitHub
2. Go to [Render Dashboard](https://dashboard.render.com) → **New** → **Web Service**
3. Connect the repo
4. Settings:
   - **Runtime**: Docker
   - **Instance Type**: Free
5. Deploy

### 4. Usage

**Health check**
```
GET https://your-app.onrender.com/
```

**Get direct download URLs (fast)**
```
GET https://your-app.onrender.com/get-url?url=https://www.youtube.com/watch?v=VIDEO_ID
```

Optional quality limit:
```
GET /get-url?url=...&quality=720
```

**Get video info**
```
GET /info?url=https://www.youtube.com/watch?v=VIDEO_ID
```

### Response Example

```json
{
  "success": true,
  "count": 2,
  "urls": [
    "https://rr5---sn-xxx.googlevideo.com/videoplayback?...",
    "https://rr5---sn-xxx.googlevideo.com/videoplayback?..."
  ],
  "note": "If 2 URLs → video + audio (merge with ffmpeg). If 1 URL → already merged."
}
```

## Keep Free Tier Alive

Render free instances sleep after inactivity.  
Use [cron-job.org](https://cron-job.org) to ping your `/` endpoint every 5–10 minutes.

## Security Tip

If your GitHub repo is public, do **not** commit the real `wireproxy.conf` with your PrivateKey.  
You can upload it as a **Secret File** on Render instead.

## License

MIT – use freely.
