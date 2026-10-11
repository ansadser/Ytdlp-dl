from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import JSONResponse
import httpx
import os

app = FastAPI(title="Cobalt GET Wrapper")

# Your existing Cobalt API URL
COBALT_API = os.getenv("COBALT_API", "https://coblt-api-pfqx.onrender.com/")


@app.get("/")
def home():
    return {
        "status": "ok",
        "usage": "/api/download?url=YOUTUBE_URL"
    }


@app.get("/api/download")
async def download(url: str = Query(..., description="Video URL")):
    """
    Simple GET endpoint.
    Example: /api/download?url=https://youtu.be/xxxxx
    Returns JSON with download URL.
    """
    if not url.startswith("http"):
        raise HTTPException(status_code=400, detail="Invalid URL")

    payload = {
        "url": url
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                COBALT_API,
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                }
            )

        data = resp.json()

        if resp.status_code != 200:
            return JSONResponse(
                status_code=resp.status_code,
                content={"success": False, "error": data}
            )

        # Success
        return {
            "success": True,
            "status": data.get("status"),
            "url": data.get("url"),
            "filename": data.get("filename"),
            "raw": data
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
