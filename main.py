from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import JSONResponse
import asyncio
import httpx
from random import choice

app = FastAPI()

# ===== CONFIG =====
PLACE_ID = 109983668079237  # ID do jogo
POOL_REFRESH_INTERVAL = 60  # segundos entre atualizações
job_pool = []  # armazenará job_ids ativos em memória

# ===== ESTRUTURA DE DADOS =====
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
    JobId: str | None = None

# ===== ROTAS =====
@app.get("/")
def get_all():
    return data

@app.get("/{tier}")
def get_tier(tier: str):
    if tier not in data:
        return {"error": "Bloco não encontrado"}
    return data[tier]

@app.post("/{tier}")
def add_entry(tier: str, item: BlockData):
    if tier not in data:
        return {"error": "Bloco inválido"}
    entry = item.dict()
    data[tier].append(entry)

    # Adiciona JobId ao pool (caso tenha vindo)
    if entry.get("JobId"):
        job_pool.append(entry["JobId"])

    return {"status": "added", "tier": tier, "entry": entry}

@app.get("/get-job")
async def get_job():
    global job_pool
    if not job_pool:
        return JSONResponse({"error": "Nenhum job_id disponível ainda"})
    job_id = choice(job_pool)
    job_pool.remove(job_id)
    return JSONResponse({"job_id": job_id})

# ===== ATUALIZAÇÃO DO POOL =====
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
                    current_jobs = [server["id"] for server in result["data"]]
                    job_pool = list(set(job_pool) | set(current_jobs))
                    print(f"[POOL] Atualizado com {len(job_pool)} JobIds ativos")
        except Exception as e:
            print("Erro ao atualizar job_pool:", e)
        await asyncio.sleep(POOL_REFRESH_INTERVAL)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(update_job_pool())
    print("[API] Job pool updater iniciado.")
