# main.py
import asyncio
from random import choice

import httpx
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()

# Configurações
PLACE_ID = 12345678  # Coloque aqui o ID do seu jogo Roblox
POOL_REFRESH_INTERVAL = 30  # Intervalo em segundos para atualizar a job_pool
job_pool = []  # Lista global de job_ids

@app.on_event("startup")
async def startup_event():
    # Inicializa a atualização contínua da job_pool
    asyncio.create_task(update_job_pool())

@app.get("/get-job")
async def get_job():
    global job_pool
    if not job_pool:
        return JSONResponse({"error": "Nenhum job_id disponível ainda"})
    job_id = choice(job_pool)
    job_pool.remove(job_id)
    return JSONResponse({"job_id": job_id})

async def update_job_pool():
    global job_pool
    while True:
        try:
            async with httpx.AsyncClient() as client:
                url = f"https://games.roblox.com/v1/games/{PLACE_ID}/servers/Public?sortOrder=Asc&limit=100"
                r = await client.get(url)
                r.raise_for_status()
                data = r.json()
                if "data" in data:
                    current_jobs = [server["id"] for server in data["data"] if server["playing"] < server["maxPlayers"]]
                    # Atualiza a job_pool sem duplicatas
                    job_pool = list(set(job_pool) | set(current_jobs))
        except Exception as e:
            print("Erro ao atualizar job_pool:", e)
        await asyncio.sleep(POOL_REFRESH_INTERVAL)
