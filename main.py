from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json
import os

app = FastAPI()

DATA_FILE = "data.json"

# Estrutura base com 6 blocos
DEFAULT_DATA = {
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

# Carregar ou criar o arquivo JSON
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
else:
    data = DEFAULT_DATA
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

@app.get("/")
def get_all():
    return data

@app.get("/{tier}")
def get_tier(tier: str):
    if tier not in data:
        raise HTTPException(status_code=404, detail="Bloco não encontrado")
    return data[tier]

@app.post("/{tier}")
def add_entry(tier: str, item: BlockData):
    if tier not in data:
        raise HTTPException(status_code=404, detail="Bloco inválido")

    data[tier].append(item.dict())

    # Salvar novamente no arquivo
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    return {"status": "added", "tier": tier, "entry": item.dict()}
