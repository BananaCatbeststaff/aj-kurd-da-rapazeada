from fastapi import FastAPI
from fastapi.responses import JSONResponse
import httpx
from random import choice
import time

app = FastAPI()

PLACE_ID = 109983668079237
POOL_REFRESH_INTERVAL = 30  # segundos

job_pool = []
last_update = 0


async def fetch_jobs():
    global job_pool, last_update

    now = time.time()
    if now - last_update < POOL_REFRESH_INTERVAL and job_pool:
        return

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            url = f"https://games.roblox.com/v1/games/{PLACE_ID}/servers/Public?sortOrder=Asc&limit=100"
            r = await client.get(url)
            r.raise_for_status()

            data = r.json().get("data", [])
            job_pool = [server["id"] for server in data]
            last_update = now

    except Exception as e:
        print("Erro ao buscar jobs:", e)


@app.get("/api")
async def get_job():
    await fetch_jobs()

    if not job_pool:
        return JSONResponse(
            {"error": "Nenhum job_id disponível"},
            status_code=503
        )

    job_id = choice(job_pool)
    job_pool.remove(job_id)

    return {"job_id": job_id}


@app.get("/")
async def root():
    return {"info": "Use /api"}
