from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import asyncio, httpx
from random import choice

app = FastAPI()

# ====== Configurações ======
PLACE_ID = "109983668079237"  # substitua pelo seu PlaceID
POOL_REFRESH_INTERVAL = 30  # segundos entre atualizações do job_pool
job_pool = []  # pool de Job IDs

# Estrutura inicial dos blocos
data = {
    "1M": [],
    "5M": [],
    "10M": [],
    "50M": [],
    "100M": [],
    "300M": []
}

# Modelo de entrada para POST
class BlockData(BaseModel):
    Name: str
    Gen: str
    Traits: str
    Mutation: str
    JobId: str  # adiciona JobId ao payload

# ====== Rotas GET ======
@app.get("/")
def get_all():
    return data

@app.get("/{tier}")
def get_tier(tier: str):
    if tier not in data:
        return {"error": "Bloco não encontrado"}
    return data[tier]

# ====== Rota POST ======
@app.post("/{tier}")
def add_entry(tier: str, item: BlockData):
    if tier not in data:
        return {"error": "Bloco inválido"}
    data[tier].append(item.dict())
    return {"status": "added", "tier": tier, "entry": item.dict()}

# ====== GET JOB ======
@app.get("/get-job")
async def get_job():
    global job_pool
    if not job_pool:
        return JSONResponse({"error": "Nenhum job_id disponível ainda"})
    job_id = choice(job_pool)
    job_pool.remove(job_id)
    return JSONResponse({"job_id": job_id})

# ====== Atualização automática do pool de servidores ======
async def update_job_pool():
    global job_pool
    while True:
        try:
            async with httpx.AsyncClient() as client:
                url = f"https://games.roblox.com/v1/games/{PLACE_ID}/servers/Public?sortOrder=Asc&limit=100"
                r = await client.get(url)
                r.raise_for_status()
                result = r.json()
                if "data" in result:
                    current_jobs = [server["id"] for server in result["data"] if server["playing"] < server["maxPlayers"]]
                    job_pool = list(set(current_jobs) | set(job_pool))
        except Exception as e:
            print("Erro ao atualizar job_pool:", e)
        await asyncio.sleep(POOL_REFRESH_INTERVAL)

# ====== Inicializa atualização automática ======
asyncio.create_task(update_job_pool())
