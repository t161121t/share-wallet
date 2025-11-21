from fastapi import FastAPI
from app.routers import transactions, stats

app = FastAPI(title="ShareWallet API")

# ルーターを登録
app.include_router(transactions.router)
app.include_router(stats.router)

@app.get("/health")
def health():
    return {"status": "ok"}