from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from models.chat import ChatResponse

from routes.chat import router

app = FastAPI(title="BIS SmartAssist API")
origins = [
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {
        "message": "BIS SmartAssist Backend is running"
    }


app.include_router(router, prefix="/api")