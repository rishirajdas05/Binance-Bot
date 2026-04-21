import sys
import os
import time
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.client import get_client
from src.logger import get_logger
from src.validator import validate_symbol, validate_grid_params, ValidationError

logger = get_logger("grid_strategy")


class GridStrategy:
    """
    Grid trading: places buy/sell limit orders across a price range.
    When a buy fills → places a sell one step up.
    When a sell fills → places a buy one step down.

    Args:
        symbol:            Trading pair.
        lower_price:       Bottom of the grid.
        upper_price:       Top of the grid.
        grids:             Number of intervals.
        quantity_per_grid: Qty per order.
        max_cycles:        Stop after N round-trips (0 = infinite).
        poll_interval:     Seconds between order checks.
    """
    def __init__(self, symbol, lower_price, upper_price, grids,
                 quantity_per_grid, max_cycles=0, poll_interval=10):
        self.symbol            = validate_symbol(symbol)
        validate_grid_params(lower_price, upper_price, grids, quantity_per_grid)
        self.lower_price       = lower_price
        self.upper_price       = upper_price
        self.grids             = grids
        self.quantity_per_grid = quantity_per_grid
        self.max_cycles        = max_cycles
        self.poll_interval     = poll_interval
        self.step_size         = (upper_price - lower_price) / grids
        self.grid_levels       = [round(lower_price + i * self.step_size, 8) for i in range(grids + 1)]
        self.active_orders     = {}
        self.total_profit_usdt = 0.0
        self.round_trips       = 0
        self._running          = False
        logger.info(
            f"Grid initialized | {self.symbol} | {lower_price}–{upper_price} | "
            f"Grids: {grids} | Step: {self.step_size:.2f} | Levels: {self.grid_levels}"
        )

    def stop(self):
        self._running = False

    def _get_current_price(self, client) -> float:
        data = client.mark_price(symbol=self.symbol)
        if isinstance(data, list):
            data = data[0]
        return float(data["markPrice"])

    def _place_order(self, client, side, price, level_index):
        try:
            response = client.new_order(
                symbol=self.symbol, side=side, order_type="LIMIT",
                quantity=self.quantity_per_grid,
                price=round(price, 2), timeInForce="GTC",
            )
            oid = response["orderId"]
            self.active_orders[oid] = {"side": side, "price": price, "level_index": level_index}
            logger.info(f"Grid order | {side} @ {price} | Level: {level_index} | OrderID: {oid}")
        except Exception as exc:
            logger.error(f"Failed to place grid {side} @ {price}: {exc}")

    def _cancel_all(self, client):
        for oid in list(self.active_orders.keys()):
            try:
                client.cancel_order(symbol=self.symbol, orderId=oid)
                logger.info(f"Cancelled {oid}")
            except Exception as exc:
                logger.warning(f"Could not cancel {oid}: {exc}")
        self.active_orders.clear()

    def _initialize_grid(self, client, current_price):
        logger.info(f"Initializing grid | CurrentPrice: {current_price}")
        for i, level in enumerate(self.grid_levels):
            if level < current_price and i < len(self.grid_levels) - 1:
                self._place_order(client, "BUY", level, i)
            elif level > current_price and i > 0:
                self._place_order(client, "SELL", level, i)
        logger.info(f"Grid ready with {len(self.active_orders)} orders.")

    def run(self) -> dict:
        client = get_client()
        self._running = True
        current_price = self._get_current_price(client)
        logger.info(f"Mark price: {current_price}")
        self._initialize_grid(client, current_price)
        logger.info("Grid running. Press Ctrl+C to stop.")

        while self._running:
            if self.max_cycles and self.round_trips >= self.max_cycles:
                logger.info(f"max_cycles ({self.max_cycles}) reached.")
                break

            filled = []
            for oid, meta in list(self.active_orders.items()):
                try:
                    status = client.query_order(symbol=self.symbol, orderId=oid).get("status")
                    if status == "FILLED":
                        filled.append((oid, meta))
                        logger.info(f"FILLED | {meta['side']} @ {meta['price']} | OrderID: {oid}")
                except Exception as exc:
                    logger.warning(f"Could not query {oid}: {exc}")

            for oid, meta in filled:
                del self.active_orders[oid]
                level_idx = meta["level_index"]
                if meta["side"] == "BUY":
                    next_idx = level_idx + 1
                    if next_idx < len(self.grid_levels):
                        self._place_order(client, "SELL", self.grid_levels[next_idx], next_idx)
                        self.total_profit_usdt += self.step_size * self.quantity_per_grid
                        logger.info(f"Counter SELL placed | Total profit: ${self.total_profit_usdt:.4f}")
                elif meta["side"] == "SELL":
                    prev_idx = level_idx - 1
                    if prev_idx >= 0:
                        self._place_order(client, "BUY", self.grid_levels[prev_idx], prev_idx)
                        self.round_trips += 1
                        logger.info(f"Counter BUY placed | RoundTrips: {self.round_trips}")

            time.sleep(self.poll_interval)

        self._cancel_all(client)
        summary = {
            "symbol": self.symbol, "range": f"{self.lower_price}–{self.upper_price}",
            "grids": self.grids, "quantity_per_grid": self.quantity_per_grid,
            "round_trips": self.round_trips,
            "estimated_profit_usdt": round(self.total_profit_usdt, 4),
        }
        logger.info(f"Grid ended | {summary}")
        return summary


if __name__ == "__main__":
    if len(sys.argv) != 6:
        print("Usage: python src/advanced/grid_strategy.py <SYMBOL> <LOWER> <UPPER> <GRIDS> <QTY_PER_GRID>")
        sys.exit(1)
    grid = GridStrategy(sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), int(sys.argv[4]), float(sys.argv[5]))
    try:
        result = grid.run()
        print(json.dumps(result, indent=2))
    except (ValidationError, KeyboardInterrupt):
        grid.stop()
    except Exception as e:
        logger.critical(f"{e}")
        sys.exit(1)