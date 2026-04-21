import os
import time
import hmac
import hashlib
import requests
from src.logger import get_logger

logger = get_logger("client")

BASE_URL = "https://demo-fapi.binance.com"

def get_credentials():
    api_key    = os.environ.get("BINANCE_API_KEY", "")
    api_secret = os.environ.get("BINANCE_API_SECRET", "")
    if not api_key or not api_secret:
        raise EnvironmentError("Missing BINANCE_API_KEY or BINANCE_API_SECRET.")
    return api_key, api_secret


def get_server_time():
    """Get Binance server time to avoid timestamp mismatch."""
    try:
        resp = requests.get(f"{BASE_URL}/fapi/v1/time", timeout=5)
        return resp.json()["serverTime"]
    except Exception:
        return int(time.time() * 1000)


def sign(params: dict, secret: str) -> dict:
    query     = "&".join(f"{k}={v}" for k, v in params.items())
    signature = hmac.new(secret.encode(), query.encode(), hashlib.sha256).hexdigest()
    params["signature"] = signature
    return params


def new_order(symbol, side, order_type, quantity, price=None,
              stopPrice=None, timeInForce=None, reduceOnly=None):
    api_key, api_secret = get_credentials()
    logger.info("Connecting to Binance Futures DEMO.")

    params = {
        "symbol":    symbol,
        "side":      side,
        "type":      order_type,
        "quantity":  quantity,
        "timestamp": get_server_time(),  # Use server time
    }
    if price:       params["price"]       = price
    if stopPrice:   params["stopPrice"]   = stopPrice
    if timeInForce: params["timeInForce"] = timeInForce
    if reduceOnly:  params["reduceOnly"]  = reduceOnly

    params   = sign(params, api_secret)
    headers  = {"X-MBX-APIKEY": api_key}
    response = requests.post(
        f"{BASE_URL}/fapi/v1/order",
        params=params,
        headers=headers,
        timeout=10,
    )
    data = response.json()
    if "code" in data and data["code"] != 200:
        raise Exception(f"({response.status_code}, {data['code']}, '{data.get('msg')}')")
    logger.info(f"Order response: {data}")
    return data


def new_algo_order(symbol, side, order_type, quantity, price=None,
                   stopPrice=None, timeInForce=None, reduceOnly=None):
    api_key, api_secret = get_credentials()
    logger.info("Placing ALGO order.")

    params = {
        "symbol":    symbol,
        "side":      side,
        "type":      order_type,
        "quantity":  quantity,
        "timestamp": get_server_time(),
    }
    if price:       params["price"]       = price
    if stopPrice:   params["stopPrice"]   = stopPrice
    if timeInForce: params["timeInForce"] = timeInForce
    if reduceOnly:  params["reduceOnly"]  = reduceOnly

    params   = sign(params, api_secret)
    headers  = {"X-MBX-APIKEY": api_key}
    response = requests.post(
        f"{BASE_URL}/fapi/v1/order/algo",
        params=params,
        headers=headers,
        timeout=10,
    )
    data = response.json()
    if "code" in data and data["code"] != 200:
        raise Exception(f"({response.status_code}, {data['code']}, '{data.get('msg')}')")
    logger.info(f"Algo order response: {data}")
    return data


def cancel_order(symbol, orderId):
    api_key, api_secret = get_credentials()
    params   = {"symbol": symbol, "orderId": orderId, "timestamp": get_server_time()}
    params   = sign(params, api_secret)
    headers  = {"X-MBX-APIKEY": api_key}
    response = requests.delete(f"{BASE_URL}/fapi/v1/order", params=params, headers=headers)
    return response.json()


def query_order(symbol, orderId):
    api_key, api_secret = get_credentials()
    params   = {"symbol": symbol, "orderId": orderId, "timestamp": get_server_time()}
    params   = sign(params, api_secret)
    headers  = {"X-MBX-APIKEY": api_key}
    response = requests.get(f"{BASE_URL}/fapi/v1/order", params=params, headers=headers)
    return response.json()


def mark_price(symbol):
    response = requests.get(
        f"{BASE_URL}/fapi/v1/premiumIndex",
        params={"symbol": symbol}
    )
    return response.json()


def get_client():
    import src.client as _self
    return _self