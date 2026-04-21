import sys
import json
from src.client import get_client
from src.logger import get_logger
from src.validator import validate_symbol, validate_side, validate_quantity, ValidationError

logger = get_logger("market_orders")


def place_market_order(symbol: str, side: str, quantity: float) -> dict:
    """
    Place a market order on Binance USDT-M Futures Demo.

    Args:
        symbol:   Trading pair, e.g. "BTCUSDT".
        side:     "BUY" or "SELL".
        quantity: Amount in base asset (e.g. 0.01 BTC).

    Returns:
        dict: Binance API response (orderId, status, avgPrice, executedQty, etc.)
    """
    symbol   = validate_symbol(symbol)
    side     = validate_side(side)
    quantity = validate_quantity(quantity)

    logger.info(f"Placing MARKET {side} order | Symbol: {symbol} | Qty: {quantity}")

    client = get_client()
    try:
        response = client.new_order(
            symbol=symbol,
            side=side,
            order_type="MARKET",
            quantity=quantity,
        )
        logger.info(
            f"Market order filled | OrderID: {response.get('orderId')} | "
            f"Status: {response.get('status')} | AvgPrice: {response.get('avgPrice')} | "
            f"FilledQty: {response.get('executedQty')}"
        )
        return response
    except Exception as exc:
        logger.error(f"Market order FAILED | {symbol} {side} | Error: {exc}")
        raise


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python src/market_orders.py <SYMBOL> <SIDE> <QUANTITY>")
        print("Example: python src/market_orders.py BTCUSDT BUY 0.01")
        sys.exit(1)
    try:
        result = place_market_order(sys.argv[1], sys.argv[2], float(sys.argv[3]))
        print(json.dumps(result, indent=2))
    except (ValidationError, Exception) as e:
        logger.critical(f"{e}")
        sys.exit(1)