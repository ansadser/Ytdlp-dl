from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import JSONResponse
import subprocess
import shutil
import socket

app = FastAPI(
    title="yt-dlp + WARP API",
    description="Fast direct stream URL extractor using yt-dlp + Cloudflare WARP",
    version="1.0.0"
)

WARP_PROXY = "socks5://127.0.0.1:1080"


def is_warp_running() -> bool:
    """Check if wireproxy SOCKS5 is listening"""
    try:
        with socket.create_connection(("127.0.0.1", 1080), timeout=2):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False


@app.get("/")
def health():
    warp_ok = is_warp_running()
    return {
        "status": "ok",
        "warp": "connected" if warp_ok else "not running",
        "yt_dlp": shutil.which("yt-dlp") is not None
    }


@app.get("/get-url")
def get_download_url(
    url: str = Query(..., description="YouTube or any yt-dlp supported URL"),
    quality: str = Query("1080", description="Max height (e.g. 720, 1080, 1440, 2160)")
):
    """
    Extract direct stream URLs only (very fast).
    Client can download the large file directly from YouTube CDN.
    """
    if not is_warp_running():
        raise HTTPException(status_code=503, detail="WARP proxy is not running")

    format_selector = f"bv*[height<={quality}]+ba/b[height<={quality}]/b"

    cmd = [
        "yt-dlp",
        "-g",                                   # get URL only (no download)
        "-f", format_selector,
        "--force-ipv4",
        "--proxy", WARP_PROXY,
        "--extractor-args", "youtube:player_client=android,web,mweb",
        "--no-warnings",
        "--no-playlist",
        url
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=45
        )

        if result.returncode == 0:
            urls = [u.strip() for u in result.stdout.strip().split("\n") if u.strip()]
            return {
                "success": True,
                "count": len(urls),
                "urls": urls,
                "note": "If 2 URLs → video + audio (merge with ffmpeg). If 1 URL → already merged."
            }
        else:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": result.stderr.strip() or "yt-dlp failed"
                }
            )

    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="yt-dlp timed out")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/info")
def get_info(url: str = Query(...)):
    """Get video metadata without downloading"""
    if not is_warp_running():
        raise HTTPException(status_code=503, detail="WARP proxy is not running")

    cmd = [
        "yt-dlp",
        "-J",                                   # JSON dump
        "--force-ipv4",
        "--proxy", WARP_PROXY,
        "--extractor-args", "youtube:player_client=android,web,mweb",
        "--no-warnings",
        "--no-playlist",
        url
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=45)
        if result.returncode == 0:
            import json
            data = json.loads(result.stdout)
            return {
                "success": True,
                "title": data.get("title"),
                "duration": data.get("duration"),
                "uploader": data.get("uploader"),
                "view_count": data.get("view_count"),
                "thumbnail": data.get("thumbnail"),
                "formats_count": len(data.get("formats", []))
            }
        else:
            return {"success": False, "error": result.stderr.strip()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
