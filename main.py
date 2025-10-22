from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import asyncio
import httpx
from random import choice

app = FastAPI()

# ====== Estrutura de blocos em memória ======
data = {
    "1M": [],
    "5M": [],
    "10M": [],
    "50M": [],
    "100M": [],
    "300M": []
}

job_pool = []
PLACE_ID = "109983668079237"  # coloque seu PlaceId
POOL_REFRESH_INTERVAL = 10  # segundos entre atualizações do job_pool

# ====== Modelo dos dados ======
class BlockData(BaseModel):
    Name: str
    Gen: str
    Traits: str
    Mutation: str
    JobId: str | None = None  # JobId opcional

# ====== Rotas da API ======
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
    data[tier].append(item.dict())
    return {"status": "added", "tier": tier, "entry": item.dict()}

# ====== Rota GET /get-job ======
@app.get("/get-job")
async def get_job():
    global job_pool
    if not job_pool:
        return JSONResponse({"error": "Nenhum job_id disponível ainda"})
    job_id = choice(job_pool)
    job_pool.remove(job_id)
    return JSONResponse({"job_id": job_id})

# ====== Atualização automática do job_pool ======
async def update_job_pool():
    global job_pool
    while True:
        try:
            async with httpx.AsyncClient() as client:
                url = f"https://games.roblox.com/v1/games/{PLACE_ID}/servers/Public?sortOrder=Asc&limit=100"
                r = await client.get(url)
                r.raise_for_status()
                resp_data = r.json()
                if "data" in resp_data:
                    current_jobs = [server["id"] for server in resp_data["data"]]
                    # combina novos jobs com os já existentes (sem duplicatas)
                    job_pool = list(set(current_jobs) | set(job_pool))
        except Exception as e:
            print("Erro ao atualizar job_pool:", e)
        await asyncio.sleep(POOL_REFRESH_INTERVAL)

# ====== Inicializa o update do job_pool ======
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(update_job_pool())
