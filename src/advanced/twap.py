"""
advanced/twap.py — TWAP strategy for Binance USDT-M Futures Demo.

Splits a large order into equal child market orders at fixed time intervals
to minimize market impact and approximate the time-weighted average price.

Example:
    BUY 0.05 BTC total, 5 intervals, 10 seconds each
    Places 0.01 BTC market order every 10s for 50 seconds total.

CLI:
    python src/advanced/twap.py BTCUSDT BUY 0.05 5 10
"""

import sys
import time
import json
import os
import threading

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.client import get_client
from src.logger import get_logger
from src.validator import validate_symbol, validate_side, validate_twap_params, ValidationError

logger = get_logger("twap")


class TWAPExecutor:
    """
    Manages execution of a TWAP strategy.

    Splits total_quantity into `intervals` equal child market orders,
    placing one every `interval_seconds` seconds.

    Attributes:
        symbol:           Trading pair.
        side:             BUY or SELL.
        total_quantity:   Total base asset to trade.
        intervals:        Number of child orders.
        interval_seconds: Delay between each child order.
        child_quantity:   Quantity per child (total / intervals).
        executed_qty:     Running total executed.
        fill_prices:      Average fill price of each successful child.
        failed_intervals: Count of failed child orders.
    """

    def __init__(self, symbol, side, total_quantity, intervals, interval_seconds):
        self.symbol           = validate_symbol(symbol)
        self.side             = validate_side(side)
        validate_twap_params(total_quantity, intervals, interval_seconds)

        self.total_quantity   = total_quantity
        self.intervals        = intervals
        self.interval_seconds = interval_seconds
        self.child_quantity   = round(total_quantity / intervals, 8)
        self.executed_qty     = 0.0
        self.fill_prices      = []
        self.failed_intervals = 0
        self._stop_event      = threading.Event()

        logger.info(
            f"TWAP initialized | {self.symbol} {self.side} | "
            f"Total: {self.total_quantity} | Intervals: {self.intervals} | "
            f"ChildQty: {self.child_quantity} | Every: {self.interval_seconds}s | "
            f"Duration: {self.intervals * self.interval_seconds}s"
        )

    def stop(self):
        """Signal the executor to stop after the current interval."""
        self._stop_event.set()

    def run(self) -> dict:
        """
        Execute the TWAP strategy.

        Places `intervals` market orders with `interval_seconds` delay between them.

        Returns:
            dict: {
                symbol, side, total_quantity, intervals,
                executed_qty, average_fill_price,
                failed_intervals, fill_prices
            }
        """
        client = get_client()
        logger.info(f"TWAP starting | {self.intervals} child orders to place.")

        for i in range(1, self.intervals + 1):
            if self._stop_event.is_set():
                logger.warning(f"TWAP halted at interval {i}/{self.intervals}.")
                break

            logger.info(
                f"TWAP [{i}/{self.intervals}] | "
                f"MARKET {self.side} {self.child_quantity} {self.symbol}"
            )

            try:
                response   = client.new_order(
                    symbol=self.symbol,
                    side=self.side,
                    order_type="MARKET",
                    quantity=self.child_quantity,
                )
                avg_price  = float(response.get("avgPrice", 0))
                filled_qty = float(response.get("executedQty", 0))

                self.executed_qty += filled_qty
                if avg_price > 0:
                    self.fill_prices.append(avg_price)

                # [OK] used instead of tick symbol — Windows cp1252 safe
                logger.info(
                    f"  [OK] OrderID: {response.get('orderId')} | "
                    f"Filled: {filled_qty} | AvgPrice: {avg_price} | "
                    f"CumulativeQty: {self.executed_qty:.8f}"
                )

            except Exception as exc:
                self.failed_intervals += 1
                logger.error(f"  [FAIL] Child order {i} FAILED: {exc}")

            if i < self.intervals and not self._stop_event.is_set():
                logger.debug(f"  Waiting {self.interval_seconds}s before next interval...")
                time.sleep(self.interval_seconds)

        avg_fill = sum(self.fill_prices) / len(self.fill_prices) if self.fill_prices else 0.0
        summary  = {
            "symbol":             self.symbol,
            "side":               self.side,
            "total_quantity":     self.total_quantity,
            "intervals":          self.intervals,
            "executed_qty":       round(self.executed_qty, 8),
            "average_fill_price": round(avg_fill, 4),
            "failed_intervals":   self.failed_intervals,
            "fill_prices":        self.fill_prices,
        }
        logger.info(
            f"TWAP complete | ExecutedQty: {summary['executed_qty']} | "
            f"AvgFill: {summary['average_fill_price']} | "
            f"Failed: {self.failed_intervals}"
        )
        return summary


def execute_twap(symbol, side, total_quantity, intervals, interval_seconds) -> dict:
    """Convenience wrapper: create and run a TWAPExecutor."""
    return TWAPExecutor(symbol, side, total_quantity, intervals, interval_seconds).run()


if __name__ == "__main__":
    if len(sys.argv) != 6:
        print("Usage: python src/advanced/twap.py "
              "<SYMBOL> <SIDE> <TOTAL_QTY> <INTERVALS> <INTERVAL_SECS>")
        print("Example: python src/advanced/twap.py BTCUSDT BUY 0.05 5 10")
        sys.exit(1)
    try:
        result = execute_twap(
            sys.argv[1], sys.argv[2],
            float(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]),
        )
        print("\n-- TWAP Summary --")
        print(json.dumps(result, indent=2))
    except (ValidationError, KeyboardInterrupt, Exception) as e:
        logger.warning(f"TWAP ended: {e}")
        sys.exit(0)