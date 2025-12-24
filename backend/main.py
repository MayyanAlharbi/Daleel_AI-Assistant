from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from utils.check_env import check_environment

from api.health import router as health_router
from api.upload import router as upload_router
from api.ask import router as ask_router
from api.summary import router as summary_router

app = FastAPI(title="Contract Understanding API")

check_environment()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(upload_router)
app.include_router(ask_router)
app.include_router(summary_router)
