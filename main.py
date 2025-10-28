from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/transactions")
async def root():
    return {"message": "Hello World"}

