import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from backend.routes import router

app = FastAPI(
    title="Генератор чертежей котлов",
    description="Параметрический генератор технических чертежей котельного оборудования",
    version="1.0.0"
)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(router)

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8080, reload=True)