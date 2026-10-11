import asyncio
import glob
import os
import re
import shutil
import tempfile
import time

import yt_dlp
from fastapi import BackgroundTasks, Depends, FastAPI, Header, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse

# ---------------- config (all from env variables) ----------------
API_KEY = os.getenv("API_KEY", "")                       # set this on Render
PLAYER_CLIENTS = os.getenv("PLAYER_CLIENTS", "tv,android_vr,web_safari").split(",")
CACHE_TTL = int(os.getenv("CACHE_TTL", "600"))           # seconds
MAX_MB = int(os.getenv("MAX_MB", "200"))                 # max download size
MAX_PARALLEL = int(os.getenv("MAX_PARALLEL", "2"))       # parallel downloads
PROXY = os.getenv("PROXY", "")                           # optional, e.g. http://127.0.0.1:25344 (WARP later)

app = FastAPI(title="YT API")
sem = asyncio.Semaphore(MAX_PARALLEL)
_cache: dict = {}


# ---------------- helpers ----------------
def check_key(x_api_key: str = Header(default="")):
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="bad api key")


def check_url(url: str):
    if not re.match(r"^https?://", url):
        raise HTTPException(status_code=400, detail="invalid url")


def base_opts() -> dict:
    opts = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "socket_timeout": 20,
        "retries": 3,
        "js_runtimes": {"node": {}},
        "extractor_args": {"youtube": {"player_client": PLAYER_CLIENTS}},
    }
    if PROXY:
        opts["proxy"] = PROXY
    return opts


def cache_get(key):
    item = _cache.get(key)
    if item and time.time() - item[0] < CACHE_TTL:
        return item[1]
    _cache.pop(key, None)
    return None


def cache_set(key, value):
    if len(_cache) > 500:
        _cache.clear()
    _cache[key] = (time.time(), value)


def format_selector(q: str) -> str:
    if q == "audio":
        return "bestaudio[ext=m4a]/bestaudio/best"
    h = int(q)
    return (
        f"bv*[height<={h}][ext=mp4]+ba[ext=m4a]"
        f"/b[height<={h}][ext=mp4]/b[height<={h}]/b"
    )


# ---------------- endpoints ----------------
@app.get("/health")
def health():
    return {"ok": True}


@app.get("/info", dependencies=[Depends(check_key)])
def info(url: str = Query(...)):
    check_url(url)
    hit = cache_get(("info", url))
    if hit:
        return hit
    try:
        with yt_dlp.YoutubeDL(base_opts()) as ydl:
            d = ydl.extract_info(url, download=False)
    except yt_dlp.utils.DownloadError as e:
        raise HTTPException(status_code=502, detail=str(e)[:300])

    heights = sorted({f["height"] for f in d.get("formats", []) if f.get("height")})
    result = {
        "id": d.get("id"),
        "title": d.get("title"),
        "uploader": d.get("uploader"),
        "duration": d.get("duration"),
        "thumbnail": d.get("thumbnail"),
        "heights": heights,
    }
    cache_set(("info", url), result)
    return result


@app.get("/dl", dependencies=[Depends(check_key)])
async def dl(
    bg: BackgroundTasks,
    url: str = Query(...),
    q: str = Query("360", pattern="^(audio|144|240|360|480|720|1080)$"),
):
    check_url(url)
    async with sem:
        tmp = tempfile.mkdtemp(prefix="ytdl_")
        opts = base_opts()
        opts.update({
            "format": format_selector(q),
            "outtmpl": f"{tmp}/%(id)s.%(ext)s",
            "merge_output_format": "mp4",
            "max_filesize": MAX_MB * 1024 * 1024,
        })
        loop = asyncio.get_running_loop()

        def run():
            with yt_dlp.YoutubeDL(opts) as ydl:
                return ydl.extract_info(url, download=True)

        try:
            d = await loop.run_in_executor(None, run)
        except yt_dlp.utils.DownloadError as e:
            shutil.rmtree(tmp, ignore_errors=True)
            raise HTTPException(status_code=502, detail=str(e)[:300])

    files = glob.glob(f"{tmp}/*")
    if not files:
        shutil.rmtree(tmp, ignore_errors=True)
        raise HTTPException(status_code=413, detail="file too large or not found")

    path = files[0]
    ext = os.path.splitext(path)[1]
    title = re.sub(r'[\\/:*?"<>|]', "_", d.get("title") or "video")[:80]
    bg.add_task(shutil.rmtree, tmp, True)
    return FileResponse(path, filename=f"{title}{ext}")
