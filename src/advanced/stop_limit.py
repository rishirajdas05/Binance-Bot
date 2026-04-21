"""
advanced/stop_limit.py — Stop-Limit orders for Binance USDT-M Futures Demo.

Binance Demo does not support STOP or TAKE_PROFIT order types.
This module simulates stop-limit behavior entirely in Python:
    1. Polls the mark price every `poll_interval` seconds.
    2. When price crosses the stop_price, places a LIMIT order at limit_price.

This is functionally identical to a real stop-limit order.

CLI:
    python src/advanced/stop_limit.py BTCUSDT SELL 0.01 76000 75000
    python src/advanced/stop_limit.py BTCUSDT BUY  0.01 77000 77500
"""

import sys
import json
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.client import get_client
from src.logger import get_logger
from src.validator import (
    validate_symbol, validate_side, validate_quantity,
    validate_price, validate_stop_limit, ValidationError,
)

logger = get_logger("stop_limit")


def place_stop_limit_order(
    symbol: str,
    side: str,
    quantity: float,
    stop_price: float,
    limit_price: float,
    time_in_force: str = "GTC",
    reduce_only: bool = False,
    poll_interval: int = 3,
) -> dict:
    """
    Simulate a Stop-Limit order by polling mark price and firing a
    LIMIT order when stop_price is triggered.

    Args:
        symbol:         Trading pair (e.g. "BTCUSDT").
        side:           "BUY" or "SELL".
        quantity:       Order size in base asset.
        stop_price:     Price that triggers the limit order.
        limit_price:    Price at which the limit order executes.
        time_in_force:  GTC | IOC | FOK (default GTC).
        reduce_only:    Only reduce an existing position if True.
        poll_interval:  Seconds between price checks (default 3).

    Returns:
        dict: Binance API response from the triggered limit order.

    Price logic:
        SELL: triggers when mark price <= stop_price (price dropped to stop)
              e.g. stop=76000, limit=75000
        BUY:  triggers when mark price >= stop_price (price rose to stop)
              e.g. stop=77000, limit=77500
    """
    symbol      = validate_symbol(symbol)
    side        = validate_side(side)
    quantity    = validate_quantity(quantity)
    stop_price  = validate_price(stop_price,  label="Stop price")
    limit_price = validate_price(limit_price, label="Limit price")
    validate_stop_limit(stop_price, limit_price, side)

    client = get_client()

    logger.info(
        f"Stop-limit MONITOR started | {side} {symbol} | Qty: {quantity} | "
        f"StopPrice: {stop_price} | LimitPrice: {limit_price} | "
        f"Polling every {poll_interval}s"
    )

    # ── Poll until stop price is hit ───────────────────────────────────────
    while True:
        try:
            data         = client.mark_price(symbol=symbol)
            if isinstance(data, list):
                data = data[0]
            current_price = float(data["markPrice"])
            logger.debug(f"Mark price: {current_price} | Waiting for stop: {stop_price}")

            triggered = (
                (side == "SELL" and current_price <= stop_price) or
                (side == "BUY"  and current_price >= stop_price)
            )

            if triggered:
                logger.info(
                    f"Stop TRIGGERED | MarkPrice: {current_price} crossed {stop_price} | "
                    f"Placing LIMIT {side} @ {limit_price}"
                )
                break

        except Exception as exc:
            logger.error(f"Price poll error: {exc}")

        time.sleep(poll_interval)

    # ── Place the limit order ──────────────────────────────────────────────
    try:
        params = dict(
            symbol=symbol,
            side=side,
            order_type="LIMIT",
            quantity=quantity,
            price=limit_price,
            timeInForce=time_in_force,
        )
        if reduce_only:
            params["reduceOnly"] = "true"

        response = client.new_order(**params)
        logger.info(
            f"Stop-limit triggered & filled | OrderID: {response.get('orderId')} | "
            f"Status: {response.get('status')} | Price: {limit_price}"
        )
        return response

    except Exception as exc:
        logger.error(f"Stop-limit LIMIT order FAILED after trigger | Error: {exc}")
        raise


if __name__ == "__main__":
    if len(sys.argv) < 6:
        print("Usage: python src/advanced/stop_limit.py "
              "<SYMBOL> <SIDE> <QTY> <STOP_PRICE> <LIMIT_PRICE> [TIF]")
        print("Example: python src/advanced/stop_limit.py BTCUSDT SELL 0.01 76000 75000")
        sys.exit(1)
    try:
        result = place_stop_limit_order(
            sys.argv[1], sys.argv[2], float(sys.argv[3]),
            float(sys.argv[4]), float(sys.argv[5]),
            sys.argv[6] if len(sys.argv) > 6 else "GTC",
        )
        print(json.dumps(result, indent=2))
    except (ValidationError, KeyboardInterrupt) as e:
        logger.warning(f"Stop-limit cancelled: {e}")
        sys.exit(0)
    except Exception as e:
        logger.critical(f"{e}")
        sys.exit(1)