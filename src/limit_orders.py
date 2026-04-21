import sys
import json
from src.client import get_client
from src.logger import get_logger
from src.validator import (
    validate_symbol, validate_side, validate_quantity,
    validate_price, ValidationError,
)

logger = get_logger("limit_orders")

VALID_TIF = {"GTC", "IOC", "FOK", "GTX"}


def place_limit_order(
    symbol: str,
    side: str,
    quantity: float,
    price: float,
    time_in_force: str = "GTC",
) -> dict:
    """
    Place a limit order on Binance USDT-M Futures Demo.

    Args:
        symbol:         Trading pair.
        side:           "BUY" or "SELL".
        quantity:       Amount in base asset.
        price:          Limit price.
        time_in_force:  GTC | IOC | FOK | GTX (default GTC)

    Returns:
        dict: Binance API response.
    """
    symbol        = validate_symbol(symbol)
    side          = validate_side(side)
    quantity      = validate_quantity(quantity)
    price         = validate_price(price, label="Limit price")
    time_in_force = time_in_force.strip().upper()

    if time_in_force not in VALID_TIF:
        raise ValidationError(f"Invalid TIF '{time_in_force}'. Must be one of {VALID_TIF}.")

    logger.info(
        f"Placing LIMIT {side} | Symbol: {symbol} | Qty: {quantity} | "
        f"Price: {price} | TIF: {time_in_force}"
    )

    client = get_client()
    try:
        response = client.new_order(
            symbol=symbol,
            side=side,
            order_type="LIMIT",
            quantity=quantity,
            price=price,
            timeInForce=time_in_force,
        )
        logger.info(
            f"Limit order placed | OrderID: {response.get('orderId')} | "
            f"Status: {response.get('status')} | Price: {response.get('price')}"
        )
        return response
    except Exception as exc:
        logger.error(f"Limit order FAILED | {symbol} {side} @ {price} | Error: {exc}")
        raise


def cancel_limit_order(symbol: str, order_id: int) -> dict:
    """Cancel an open limit order by order ID."""
    symbol = validate_symbol(symbol)
    logger.info(f"Cancelling order | Symbol: {symbol} | OrderID: {order_id}")
    client = get_client()
    try:
        response = client.cancel_order(symbol=symbol, orderId=order_id)
        logger.info(f"Order cancelled | OrderID: {order_id} | Status: {response.get('status')}")
        return response
    except Exception as exc:
        logger.error(f"Cancel FAILED | OrderID: {order_id} | Error: {exc}")
        raise


def query_order_status(symbol: str, order_id: int) -> dict:
    """Query the current status of an order."""
    symbol = validate_symbol(symbol)
    logger.info(f"Querying order | Symbol: {symbol} | OrderID: {order_id}")
    client = get_client()
    try:
        response = client.query_order(symbol=symbol, orderId=order_id)
        logger.info(
            f"Order status | OrderID: {order_id} | Status: {response.get('status')} | "
            f"FilledQty: {response.get('executedQty')}"
        )
        return response
    except Exception as exc:
        logger.error(f"Query FAILED | OrderID: {order_id} | Error: {exc}")
        raise


if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Usage: python src/limit_orders.py <SYMBOL> <SIDE> <QUANTITY> <PRICE> [TIF]")
        print("Example: python src/limit_orders.py BTCUSDT BUY 0.01 30000 GTC")
        sys.exit(1)
    try:
        result = place_limit_order(
            sys.argv[1], sys.argv[2], float(sys.argv[3]),
            float(sys.argv[4]), sys.argv[5] if len(sys.argv) > 5 else "GTC"
        )
        print(json.dumps(result, indent=2))
    except (ValidationError, Exception) as e:
        logger.critical(f"{e}")
        sys.exit(1)