"""
bot.py — Unified CLI entry-point for the Binance Futures Order Bot.

Usage:
    python bot.py market  BTCUSDT BUY  0.01
    python bot.py limit   BTCUSDT BUY  0.01 30000
    python bot.py limit   BTCUSDT SELL 0.5  29000 IOC
    python bot.py stop    BTCUSDT SELL 0.01 76000 75000
    python bot.py oco     BTCUSDT SELL 0.01 90000 74000 73500
    python bot.py twap    BTCUSDT BUY  0.05 5 10
    python bot.py grid    BTCUSDT 74000 80000 5 0.001
"""

import sys
import json
import argparse
from dotenv import load_dotenv
from src.logger import get_logger

# Load .env file first before anything else
load_dotenv()

logger = get_logger("bot")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bot.py",
        description="Binance USDT-M Futures Testnet Order Bot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python bot.py market  BTCUSDT BUY  0.01
  python bot.py limit   BTCUSDT BUY  0.01 30000
  python bot.py limit   BTCUSDT SELL 0.5  29000 IOC
  python bot.py stop    BTCUSDT SELL 0.01 76000 75000
  python bot.py oco     BTCUSDT SELL 0.01 90000 74000 73500
  python bot.py twap    BTCUSDT BUY  0.05 5 10
  python bot.py grid    BTCUSDT 74000 80000 5 0.001
""",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # market
    p = sub.add_parser("market", help="Market order — executes immediately at best price")
    p.add_argument("symbol");  p.add_argument("side")
    p.add_argument("quantity", type=float)

    # limit
    p = sub.add_parser("limit", help="Limit order — executes at specified price or better")
    p.add_argument("symbol");  p.add_argument("side")
    p.add_argument("quantity", type=float)
    p.add_argument("price",    type=float)
    p.add_argument("tif",      nargs="?", default="GTC",
                   help="GTC|IOC|FOK|GTX (default: GTC)")

    # stop-limit
    p = sub.add_parser("stop", help="Stop-limit order — limit order triggered at stop price")
    p.add_argument("symbol");  p.add_argument("side")
    p.add_argument("quantity",    type=float)
    p.add_argument("stop_price",  type=float)
    p.add_argument("limit_price", type=float)

    # oco
    p = sub.add_parser("oco", help="OCO — simultaneous take-profit + stop-loss")
    p.add_argument("symbol");  p.add_argument("side")
    p.add_argument("quantity",         type=float)
    p.add_argument("take_profit",      type=float)
    p.add_argument("stop_price",       type=float)
    p.add_argument("stop_limit_price", type=float)

    # twap
    p = sub.add_parser("twap", help="TWAP — split large order over time")
    p.add_argument("symbol");  p.add_argument("side")
    p.add_argument("total_qty",        type=float)
    p.add_argument("intervals",        type=int)
    p.add_argument("interval_seconds", type=int)

    # grid
    p = sub.add_parser("grid", help="Grid — automated buy-low/sell-high within a range")
    p.add_argument("symbol")
    p.add_argument("lower_price",  type=float)
    p.add_argument("upper_price",  type=float)
    p.add_argument("grids",        type=int)
    p.add_argument("qty_per_grid", type=float)

    return parser


def main():
    parser = build_parser()
    args   = parser.parse_args()
    logger.info(f"Bot command: {args.command} | Args: {vars(args)}")

    try:
        if args.command == "market":
            from src.market_orders import place_market_order
            result = place_market_order(args.symbol, args.side, args.quantity)
            print(json.dumps(result, indent=2))

        elif args.command == "limit":
            from src.limit_orders import place_limit_order
            result = place_limit_order(
                args.symbol, args.side, args.quantity, args.price, args.tif
            )
            print(json.dumps(result, indent=2))

        elif args.command == "stop":
            from src.advanced.stop_limit import place_stop_limit_order
            result = place_stop_limit_order(
                args.symbol, args.side, args.quantity,
                args.stop_price, args.limit_price,
            )
            print(json.dumps(result, indent=2))

        elif args.command == "oco":
            from src.advanced.oco import place_oco_order

            result, oco_done, sl_thread, tp_thread = place_oco_order(
                args.symbol, args.side, args.quantity,
                args.take_profit, args.stop_price, args.stop_limit_price,
            )
            print(json.dumps(result, indent=2))
            logger.info("OCO active. Waiting for TP fill or SL trigger. Press Ctrl+C to cancel.")
            oco_done.wait()
            sl_thread.join(timeout=5)
            tp_thread.join(timeout=5)
            logger.info("OCO complete.")

        elif args.command == "twap":
            from src.advanced.twap import execute_twap
            result = execute_twap(
                args.symbol, args.side,
                args.total_qty, args.intervals, args.interval_seconds,
            )
            print("\n-- TWAP Summary --")
            print(json.dumps(result, indent=2))

        elif args.command == "grid":
            from src.advanced.grid_strategy import GridStrategy
            grid = GridStrategy(
                args.symbol, args.lower_price, args.upper_price,
                args.grids, args.qty_per_grid,
            )
            result = grid.run()
            print("\n-- Grid Summary --")
            print(json.dumps(result, indent=2))

    except KeyboardInterrupt:
        logger.warning("Bot interrupted by user (Ctrl+C).")
    except Exception as exc:
        logger.critical(f"Fatal error: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()