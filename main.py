from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import httpx
import time
from random import choice
from threading import Thread

app = FastAPI()

# ====== Configurações ======
PLACE_ID = 109983668079237  # Coloque aqui o ID do seu jogo Roblox
POOL_REFRESH_INTERVAL = 60  # Intervalo em segundos para atualizar job_pool
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

@app.get("/api/get-job")
def get_job():
    global job_pool
    if not job_pool:
        return JSONResponse({"error": "Nenhum job_id disponível ainda"})
    job_id = choice(job_pool)
    job_pool.remove(job_id)
    return JSONResponse({"job_id": job_id})

# ====== Atualização da job_pool com loop síncrono ======
def update_job_pool_loop():
    global job_pool
    while True:
        try:
            url = f"https://games.roblox.com/v1/games/{PLACE_ID}/servers/Public?sortOrder=Asc&limit=100"
            r = httpx.get(url)
            r.raise_for_status()
            data_json = r.json()
            if "data" in data_json:
                current_jobs = [server["id"] for server in data_json["data"]]
                job_pool = list(set(current_jobs) | set(job_pool))
                print(f"[JobPool] Atualizada: {len(job_pool)} jobs disponíveis")
        except Exception as e:
            print("Erro ao atualizar job_pool:", e)
        time.sleep(POOL_REFRESH_INTERVAL)

# ====== Inicialização ======
def start_background_loop():
    thread = Thread(target=update_job_pool_loop, daemon=True)
    thread.start()
    print("[Startup] Loop síncrono de atualização de job_pool iniciado.")

start_background_loop()
