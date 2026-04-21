"""
orders.py — REST API routes for all order types.
Credentials loaded from .env file automatically.
"""

import os
import sys
import time
import hmac
import hashlib
import requests
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

router = APIRouter()


# ── Request models (no api_key/secret needed — loaded from .env) ──────────────

class MarketOrderRequest(BaseModel):
    symbol:   str
    side:     str
    quantity: float

class LimitOrderRequest(BaseModel):
    symbol:        str
    side:          str
    quantity:      float
    price:         float
    time_in_force: Optional[str] = "GTC"

class StopLimitOrderRequest(BaseModel):
    symbol:      str
    side:        str
    quantity:    float
    stop_price:  float
    limit_price: float

class OCOOrderRequest(BaseModel):
    symbol:            str
    side:              str
    quantity:          float
    take_profit_price: float
    stop_price:        float
    stop_limit_price:  float


# ── Helper — reads from environment (.env loaded in main.py) ───────────────────

def get_api_credentials():
    key    = os.environ.get("BINANCE_API_KEY", "")
    secret = os.environ.get("BINANCE_API_SECRET", "")
    if not key or not secret:
        raise HTTPException(
            status_code=401,
            detail="API credentials not found. Check your .env file."
        )
    return key, secret


# ── Routes ─────────────────────────────────────────────────────────────────────

@router.post("/orders/market")
def place_market(req: MarketOrderRequest):
    get_api_credentials()  # Validate creds exist
    try:
        from src.market_orders import place_market_order
        result = place_market_order(req.symbol, req.side, req.quantity)
        return {"success": True, "order": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/orders/limit")
def place_limit(req: LimitOrderRequest):
    get_api_credentials()
    try:
        from src.limit_orders import place_limit_order
        result = place_limit_order(
            req.symbol, req.side, req.quantity,
            req.price, req.time_in_force
        )
        return {"success": True, "order": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/orders/stop")
def place_stop(req: StopLimitOrderRequest):
    get_api_credentials()
    try:
        from src.advanced.stop_limit import place_stop_limit_order
        result = place_stop_limit_order(
            req.symbol, req.side, req.quantity,
            req.stop_price, req.limit_price
        )
        return {"success": True, "order": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/orders/oco")
def place_oco(req: OCOOrderRequest):
    get_api_credentials()
    try:
        from src.advanced.oco import place_oco_order
        result, oco_done, sl_thread, tp_thread = place_oco_order(
            req.symbol, req.side, req.quantity,
            req.take_profit_price, req.stop_price, req.stop_limit_price
        )
        return {"success": True, "order": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/orders/open/{symbol}")
def get_open_orders(symbol: str):
    api_key, api_secret = get_api_credentials()
    try:
        params = {"symbol": symbol.upper(), "timestamp": int(time.time() * 1000)}
        query  = "&".join(f"{k}={v}" for k, v in params.items())
        sig    = hmac.new(api_secret.encode(), query.encode(), hashlib.sha256).hexdigest()
        params["signature"] = sig
        resp = requests.get(
            "https://demo-fapi.binance.com/fapi/v1/openOrders",
            params=params,
            headers={"X-MBX-APIKEY": api_key},
        )
        return {"success": True, "orders": resp.json()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/price/{symbol}")
def get_price(symbol: str):
    try:
        resp = requests.get(
            "https://demo-fapi.binance.com/fapi/v1/premiumIndex",
            params={"symbol": symbol.upper()}
        )
        data = resp.json()
        return {"symbol": symbol.upper(), "price": float(data["markPrice"])}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/account")
def get_account():
    api_key, api_secret = get_api_credentials()
    try:
        params = {"timestamp": int(time.time() * 1000)}
        query  = "&".join(f"{k}={v}" for k, v in params.items())
        sig    = hmac.new(api_secret.encode(), query.encode(), hashlib.sha256).hexdigest()
        params["signature"] = sig
        resp = requests.get(
            "https://demo-fapi.binance.com/fapi/v2/account",
            params=params,
            headers={"X-MBX-APIKEY": api_key},
        )
        data = resp.json()
        return {
            "success":               True,
            "totalWalletBalance":    data.get("totalWalletBalance"),
            "availableBalance":      data.get("availableBalance"),
            "totalUnrealizedProfit": data.get("totalUnrealizedProfit"),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))