"""
advanced/oco.py — OCO (One-Cancels-the-Other) for Binance USDT-M Futures Demo.

Binance Demo does not support STOP or TAKE_PROFIT order types.
This module implements OCO fully in Python:
    - Leg 1: Take-profit LIMIT order placed immediately.
    - Leg 2: Stop-loss simulated by polling mark price.
      When stop_price is hit, a LIMIT order fires at stop_limit_price.
      Simultaneously, the take-profit order is cancelled.

When the take-profit fills first, the stop-loss monitor exits cleanly.

CLI:
    python src/advanced/oco.py BTCUSDT SELL 0.01 90000 74000 73500
"""

import sys
import json
import os
import time
import threading

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.client import get_client
from src.logger import get_logger
from src.validator import (
    validate_symbol, validate_side, validate_quantity,
    validate_price, ValidationError,
)

logger = get_logger("oco")


def place_oco_order(
    symbol: str,
    side: str,
    quantity: float,
    take_profit_price: float,
    stop_price: float,
    stop_limit_price: float,
    time_in_force: str = "GTC",
    poll_interval: int = 3,
) -> dict:
    """
    Simulate an OCO order on Binance USDT-M Futures Demo.

    Leg 1 — Take-profit: LIMIT order placed immediately.
    Leg 2 — Stop-loss:   Python price monitor fires a LIMIT order
                         when mark price crosses stop_price.

    Whichever triggers first cancels the other.

    Args:
        symbol:             Trading pair.
        side:               "SELL" to exit a long, "BUY" to exit a short.
        quantity:           Size of each leg.
        take_profit_price:  Limit price for the take-profit leg.
        stop_price:         Trigger price for the stop-loss leg.
        stop_limit_price:   Limit fill price for the stop-loss leg.
        time_in_force:      GTC (default).
        poll_interval:      Seconds between price checks (default 3).

    Returns:
        dict: {
            "take_profit_order": { ...Binance response... },
            "stop_loss_order":   None (filled when triggered),
            "monitor": "running in background thread"
        }

    Price ordering:
        SELL OCO: take_profit_price > stop_price > stop_limit_price
                  e.g. TP=90000, Stop=74000, StopLimit=73500
        BUY OCO:  take_profit_price < stop_price < stop_limit_price
                  e.g. TP=65000, Stop=78000, StopLimit=78500
    """
    symbol            = validate_symbol(symbol)
    side              = validate_side(side)
    quantity          = validate_quantity(quantity)
    take_profit_price = validate_price(take_profit_price, label="Take-profit price")
    stop_price        = validate_price(stop_price,        label="Stop price")
    stop_limit_price  = validate_price(stop_limit_price,  label="Stop limit price")

    if side == "SELL":
        if take_profit_price <= stop_price:
            raise ValidationError(
                f"SELL OCO: take_profit ({take_profit_price}) must be > stop_price ({stop_price})."
            )
        if stop_price <= stop_limit_price:
            raise ValidationError(
                f"SELL OCO: stop_price ({stop_price}) must be > stop_limit_price ({stop_limit_price})."
            )
    elif side == "BUY":
        if take_profit_price >= stop_price:
            raise ValidationError(
                f"BUY OCO: take_profit ({take_profit_price}) must be < stop_price ({stop_price})."
            )
        if stop_price >= stop_limit_price:
            raise ValidationError(
                f"BUY OCO: stop_price ({stop_price}) must be < stop_limit_price ({stop_limit_price})."
            )

    logger.info(
        f"Placing OCO {side} | {symbol} | Qty: {quantity} | "
        f"TP: {take_profit_price} | Stop: {stop_price} | StopLimit: {stop_limit_price}"
    )

    client = get_client()

    # ── Leg 1: Take-profit LIMIT order (placed immediately) ────────────────
    try:
        tp_order = client.new_order(
            symbol=symbol,
            side=side,
            order_type="LIMIT",
            quantity=quantity,
            price=take_profit_price,
            timeInForce=time_in_force,
            reduceOnly="true",
        )
        tp_order_id = tp_order.get("orderId")
        logger.info(f"OCO TP leg placed | OrderID: {tp_order_id} @ {take_profit_price}")
    except Exception as exc:
        logger.error(f"OCO TP leg FAILED: {exc}")
        raise

    # Shared flag between TP monitor and SL monitor
    oco_done = threading.Event()

    # ── Leg 2: Stop-loss — Python price monitor ────────────────────────────
    def stop_loss_monitor():
        logger.info(
            f"OCO SL monitor started | Watching for price cross @ {stop_price}"
        )
        while not oco_done.is_set():
            try:
                data = client.mark_price(symbol=symbol)
                if isinstance(data, list):
                    data = data[0]
                current_price = float(data["markPrice"])
                logger.debug(f"OCO SL poll | MarkPrice: {current_price} | StopAt: {stop_price}")

                triggered = (
                    (side == "SELL" and current_price <= stop_price) or
                    (side == "BUY"  and current_price >= stop_price)
                )

                if triggered and not oco_done.is_set():
                    logger.info(
                        f"OCO stop TRIGGERED | Price: {current_price} crossed {stop_price} | "
                        f"Placing SL LIMIT @ {stop_limit_price}"
                    )
                    oco_done.set()

                    # Cancel take-profit
                    try:
                        client.cancel_order(symbol=symbol, orderId=tp_order_id)
                        logger.info(f"OCO TP order {tp_order_id} cancelled (SL triggered).")
                    except Exception as ce:
                        logger.warning(f"Could not cancel TP order: {ce}")

                    # Place stop-loss limit order
                    try:
                        sl_response = client.new_order(
                            symbol=symbol,
                            side=side,
                            order_type="LIMIT",
                            quantity=quantity,
                            price=stop_limit_price,
                            timeInForce=time_in_force,
                            reduceOnly="true",
                        )
                        logger.info(
                            f"OCO SL order placed | OrderID: {sl_response.get('orderId')} | "
                            f"Price: {stop_limit_price}"
                        )
                    except Exception as se:
                        logger.error(f"OCO SL limit order FAILED: {se}")
                    return

            except Exception as exc:
                logger.error(f"OCO SL monitor error: {exc}")

            time.sleep(poll_interval)

        logger.info("OCO SL monitor exited (TP filled or cancelled).")

    # ── TP fill monitor ────────────────────────────────────────────────────
    def tp_fill_monitor():
        logger.info(f"OCO TP fill monitor started | OrderID: {tp_order_id}")
        while not oco_done.is_set():
            try:
                status = client.query_order(
                    symbol=symbol, orderId=tp_order_id
                ).get("status")
                logger.debug(f"OCO TP status: {status}")

                if status == "FILLED":
                    logger.info(f"OCO TP FILLED | OrderID: {tp_order_id}")
                    oco_done.set()
                    return

                if status in ("CANCELED", "EXPIRED"):
                    logger.info(f"OCO TP order {tp_order_id} cancelled/expired.")
                    oco_done.set()
                    return

            except Exception as exc:
                logger.error(f"OCO TP monitor error: {exc}")

            time.sleep(poll_interval)

    # Start both monitors as background threads
    sl_thread = threading.Thread(target=stop_loss_monitor, daemon=True)
    tp_thread = threading.Thread(target=tp_fill_monitor,   daemon=True)
    sl_thread.start()
    tp_thread.start()

    result = {
        "take_profit_order": tp_order,
        "stop_loss_order":   None,
        "monitor":           "running — SL triggers if price hits stop, TP fill cancels SL",
    }
    logger.info(
        f"OCO active | TP_ID: {tp_order_id} | "
        f"SL watching for price @ {stop_price} | Press Ctrl+C to cancel."
    )
    return result, oco_done, sl_thread, tp_thread


if __name__ == "__main__":
    if len(sys.argv) != 7:
        print("Usage: python src/advanced/oco.py "
              "<SYMBOL> <SIDE> <QTY> <TP_PRICE> <STOP_PRICE> <STOP_LIMIT_PRICE>")
        print("Example: python src/advanced/oco.py BTCUSDT SELL 0.01 90000 74000 73500")
        sys.exit(1)
    try:
        result, oco_done, sl_thread, tp_thread = place_oco_order(
            sys.argv[1], sys.argv[2], float(sys.argv[3]),
            float(sys.argv[4]), float(sys.argv[5]), float(sys.argv[6]),
        )
        print(json.dumps(result, indent=2))
        logger.info("OCO running. Press Ctrl+C to exit.")
        # Wait for either leg to complete
        oco_done.wait()
        sl_thread.join(timeout=5)
        tp_thread.join(timeout=5)
        logger.info("OCO complete.")
    except (ValidationError, Exception) as e:
        logger.critical(f"{e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.warning("OCO interrupted by user.")
        sys.exit(0)