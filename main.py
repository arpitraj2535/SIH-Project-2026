from fastapi import FastAPI

from models.chat import ChatResponse

from routes.chat import router

app = FastAPI(title="BIS SmartAssist API")


@app.get("/")
def home():
    return {
        "message": "BIS SmartAssist Backend is running"
    }


app.include_router(router, prefix="/api")