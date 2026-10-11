# Cobalt GET Wrapper

Simple GET API in front of your Cobalt instance.

## Usage

```
GET https://your-wrapper.onrender.com/api/download?url=https://youtu.be/xxxxx
```

### Response

```json
{
  "success": true,
  "status": "tunnel",
  "url": "https://coblt-api-pfqx.onrender.com/tunnel?...",
  "filename": "video.mp4"
}
```

## Deploy to Render

1. Push to GitHub
2. New Web Service → Docker
3. Environment Variable (optional):
   ```
   COBALT_API = https://coblt-api-pfqx.onrender.com/
   ```
4. Deploy

## Keep Alive

Ping the `/` endpoint every 5-10 minutes with cron-job.org
