"""
websocket.py — WebSocket endpoint for live price feed.
Frontend connects here to receive real-time BTC price updates.
"""

import asyncio
import requests
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()


@router.websocket("/ws/price/{symbol}")
async def price_feed(websocket: WebSocket, symbol: str):
    """
    Streams mark price for a symbol every second to the frontend.
    Frontend connects with: new WebSocket('ws://localhost:8000/ws/price/BTCUSDT')
    """
    await websocket.accept()
    try:
        while True:
            resp  = requests.get(
                "https://demo-fapi.binance.com/fapi/v1/premiumIndex",
                params={"symbol": symbol.upper()},
                timeout=5,
            )
            data  = resp.json()
            price = float(data.get("markPrice", 0))
            await websocket.send_json({"symbol": symbol.upper(), "price": price})
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.close()


@router.websocket("/ws/logs")
async def log_feed(websocket: WebSocket):
    """
    Streams new lines from bot.log to the frontend every second.
    Frontend connects with: new WebSocket('ws://localhost:8000/ws/logs')
    """
    await websocket.accept()
    import os
    log_path = "bot.log"
    try:
        with open(log_path, "r", encoding="utf-8", errors="replace") as f:
            f.seek(0, 2)  # Seek to end
            while True:
                line = f.readline()
                if line:
                    await websocket.send_text(line.strip())
                else:
                    await asyncio.sleep(0.5)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.close()