"""
main.py — FastAPI backend server for Binance Bot UI.

Run:
    uvicorn backend.main:app --reload --port 8000
"""

import os
import sys
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Load .env file FIRST before anything else
load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from backend.routes.orders     import router as orders_router
from backend.routes.strategies import router as strategies_router
from backend.routes.websocket  import router as ws_router

app = FastAPI(title="Binance Bot API", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(orders_router,     prefix="/api")
app.include_router(strategies_router, prefix="/api")
app.include_router(ws_router)

app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/")
def root():
    return FileResponse("frontend/index.html")

@app.get("/orders")
def orders_page():
    return FileResponse("frontend/orders.html")

@app.get("/strategies")
def strategies_page():
    return FileResponse("frontend/strategies.html")

@app.get("/logs")
def logs_page():
    return FileResponse("frontend/logs.html")