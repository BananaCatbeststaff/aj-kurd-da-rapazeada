from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import asyncio
from random import choice
import httpx

app = FastAPI()

# ====== Configurações ======
PLACE_ID = 12345678  # Coloque aqui o ID do seu jogo Roblox
POOL_REFRESH_INTERVAL = 30  # Intervalo para atualizar job_pool
job_pool = []  # Lista global de job_ids

# Estrutura inicial dos blocos em memória
data = {
    "1M": [],
    "5M": [],
    "10M": [],
    "50M": [],
    "100M": [],
    "300M": []
}

class BlockData(BaseModel):
    Name: str
    Gen: str
    Traits: str
    Mutation: str

# ====== Rotas API ======

# GET raiz - retorna todos os blocos
@app.get("/")
async def get_all():
    return data

# GET bloco específico
@app.get("/{tier}")
async def get_tier(tier: str):
    if tier not in data:
        return {"error": "Bloco não encontrado"}
    return data[tier]

# POST para adicionar item a um bloco
@app.post("/{tier}")
async def add_entry(tier: str, item: BlockData):
    if tier not in data:
        return {"error": "Bloco inválido"}
    data[tier].append(item.dict())
    return {"status": "added", "tier": tier, "entry": item.dict()}

# GET job_id via /api/get-job
@app.get("/api/get-job")
async def get_job():
    global job_pool
    if not job_pool:
        return JSONResponse({"error": "Nenhum job_id disponível ainda"})
    job_id = choice(job_pool)
    job_pool.remove(job_id)
    return JSONResponse({"job_id": job_id})

# ====== Atualização contínua da job_pool ======
async def update_job_pool():
    global job_pool
    while True:
        try:
            async with httpx.AsyncClient() as client:
                url = f"https://games.roblox.com/v1/games/{PLACE_ID}/servers/Public?sortOrder=Asc&limit=100"
                r = await client.get(url)
                r.raise_for_status()
                data_json = r.json()
                if "data" in data_json:
                    current_jobs = [server["id"] for server in data_json["data"]]
                    job_pool = list(set(current_jobs) | set(job_pool))
        except Exception as e:
            print("Erro ao atualizar job_pool:", e)
        await asyncio.sleep(POOL_REFRESH_INTERVAL)

# ====== Inicialização ======
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(update_job_pool())
