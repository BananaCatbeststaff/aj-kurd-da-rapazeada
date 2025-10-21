from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

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

# GET para todos os blocos
@app.get("/")
def get_all():
    return data

# GET para um bloco específico
@app.get("/{tier}")
def get_tier(tier: str):
    if tier not in data:
        return {"error": "Bloco não encontrado"}
    return data[tier]

# POST para adicionar item a um bloco
@app.post("/{tier}")
def add_entry(tier: str, item: BlockData):
    if tier not in data:
        return {"error": "Bloco inválido"}

    data[tier].append(item.dict())
    return {"status": "added", "tier": tier, "entry": item.dict()}
