from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

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
