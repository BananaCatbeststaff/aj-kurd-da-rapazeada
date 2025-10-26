from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import httpx
import time
from random import choice
from threading import Thread

app = FastAPI()

# ====== Configurações ======
PLACE_ID = 109983668079237  # ID do jogo Roblox
POOL_REFRESH_INTERVAL = 60  # Intervalo (segundos) para atualizar job_pool
MAX_BLOCKS = 30             # Máximo de blocos armazenados
job_pool = []               # Lista global de job_ids

# Estrutura principal de blocos: lista única
blocks = []

# ====== Modelo de entrada ======
class BlockData(BaseModel):
    Name: str
    Gen: str
    JobId: str

# ====== Rotas API ======

@app.get("/")
def get_all_blocks():
    """Retorna todos os blocos armazenados"""
    return {"blocks": blocks}

@app.post("/")
def add_block(item: BlockData):
    """Adiciona um novo bloco até o limite de 30"""
    entry_str = f"Name = {item.Name}, Gen = {item.Gen}, JobId = {item.JobId}"

    # Evita duplicatas
    if entry_str in blocks:
        return {"status": "ignored", "reason": "entrada duplicada"}

    # Adiciona o novo bloco
    blocks.append(entry_str)

    # Mantém no máximo MAX_BLOCKS
    if len(blocks) > MAX_BLOCKS:
        removed = blocks.pop(0)
        print(f"[Removido] {removed}")

    print(f"[Nova entrada] {entry_str}")
    return {"status": "added", "entry": entry_str, "total": len(blocks)}

@app.get("/api/get-job")
def get_job():
    """Retorna um job_id aleatório da pool"""
    global job_pool
    if not job_pool:
        return JSONResponse({"error": "Nenhum job_id disponível ainda"})
    job_id = choice(job_pool)
    job_pool.remove(job_id)
    return JSONResponse({"job_id": job_id})

# ====== Atualização da job_pool (loop síncrono) ======
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
