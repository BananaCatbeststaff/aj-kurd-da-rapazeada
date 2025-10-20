from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()

# "Banco de dados" simples em memória
data_store = []

@app.get("/")
async def root():
    return {"message": "API online ✅ - use /data para GET e POST"}

@app.get("/data")
async def get_data():
    return {"data": data_store}

@app.post("/data")
async def post_data(request: Request):
    try:
        body = await request.json()
        data_store.append(body)
        return JSONResponse(content={"status": "success", "received": body}, status_code=201)
    except Exception as e:
        return JSONResponse(content={"status": "error", "detail": str(e)}, status_code=400)
