# Binance Futures Order Bot

A fully-featured CLI trading bot for **Binance USDT-M Futures** supporting
market orders, limit orders, and four advanced strategies: **Stop-Limit**,
**OCO**, **TWAP**, and **Grid Trading**.

---

## Project Structure

```
binance_bot/
│
├── bot.py                        # Unified CLI entry-point (all order types)
├── requirements.txt
├── bot.log                       # Auto-generated structured log file
├── README.md
│
└── src/
    ├── __init__.py
    ├── client.py                 # API client factory (testnet/live)
    ├── logger.py                 # Centralized colored + file logging
    ├── validator.py              # All input validation logic
    ├── market_orders.py          # Market order execution
    ├── limit_orders.py           # Limit order execution + cancel/query
    │
    └── advanced/
        ├── __init__.py
        ├── stop_limit.py         # Stop-Limit orders
        ├── oco.py                # OCO (One-Cancels-the-Other)
        ├── twap.py               # TWAP strategy
        └── grid_strategy.py      # Grid trading strategy
```

---

## Setup

### 1. Clone / Download

```bash
git clone https://github.com/your_name/your_name-binance-bot.git
cd your_name-binance-bot
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Get Binance Testnet API Keys

1. Go to [Binance Futures Testnet](https://testnet.binancefuture.com/)
2. Log in and navigate to **API Management**
3. Generate a new API Key + Secret
4. Keep these safe — you'll need them in the next step

### 4. Set Environment Variables

**Linux / macOS:**
```bash
export BINANCE_API_KEY="your_api_key_here"
export BINANCE_API_SECRET="your_api_secret_here"
export BINANCE_TESTNET="true"      # Set to "false" for live trading
```

**Windows (PowerShell):**
```powershell
$env:BINANCE_API_KEY    = "your_api_key_here"
$env:BINANCE_API_SECRET = "your_api_secret_here"
$env:BINANCE_TESTNET    = "true"
```

> ⚠️ **Never hardcode API keys in source code. Always use environment variables.**

---

## Usage

All orders can be run via the unified `bot.py` entry-point **or** by calling
individual modules directly.

---

### Market Order

Executes immediately at the best available price.

```bash
# Via unified bot
python bot.py market BTCUSDT BUY 0.01
python bot.py market ETHUSDT SELL 0.5

# Via module directly
python src/market_orders.py BTCUSDT BUY 0.01
```

**Arguments:**
| Argument   | Description                        | Example    |
|------------|------------------------------------|------------|
| `SYMBOL`   | Trading pair (uppercase)           | `BTCUSDT`  |
| `SIDE`     | Direction                          | `BUY`/`SELL` |
| `QUANTITY` | Amount in base asset               | `0.01`     |

---

### Limit Order

Executes only at the specified price or better. Rests in the order book.

```bash
python bot.py limit BTCUSDT BUY  0.01 30000
python bot.py limit ETHUSDT SELL 1.0  2000 IOC
```

**Arguments:**
| Argument         | Description                                | Default |
|------------------|--------------------------------------------|---------|
| `SYMBOL`         | Trading pair                               |         |
| `SIDE`           | BUY or SELL                                |         |
| `QUANTITY`       | Amount in base asset                       |         |
| `PRICE`          | Limit price                                |         |
| `TIME_IN_FORCE`  | `GTC` / `IOC` / `FOK` / `GTX`             | `GTC`   |

**Time-In-Force Options:**
- **GTC** — Good Till Cancelled (stays until filled or cancelled)
- **IOC** — Immediate Or Cancel (fill what you can, cancel the rest)
- **FOK** — Fill Or Kill (fill everything or cancel entirely)
- **GTX** — Good Till Crossing / Post-Only (only maker order)

---

### Stop-Limit Order *(Advanced)*

Places a limit order only when the market price reaches the stop trigger.

```bash
# Stop-loss: Sell if BTC drops to $29,000, fill at $28,800 or better
python bot.py stop BTCUSDT SELL 0.01 29000 28800

# Breakout entry: Buy if BTC rises to $32,000, fill at $32,200 or better
python bot.py stop BTCUSDT BUY 0.01 32000 32200
```

**Arguments:**
| Argument      | Description                            |
|---------------|----------------------------------------|
| `SYMBOL`      | Trading pair                           |
| `SIDE`        | BUY or SELL                            |
| `QUANTITY`    | Amount in base asset                   |
| `STOP_PRICE`  | Price that activates the limit order   |
| `LIMIT_PRICE` | Price at which the limit order executes|

**Price Logic:**
- **SELL**: `stop_price > limit_price` (stop triggers, then fills at limit or above)
- **BUY**: `stop_price < limit_price` (stop triggers, then fills at limit or below)

---

### OCO Order *(Advanced)*

Places a take-profit and stop-loss simultaneously.
When one fills, the other is cancelled.

```bash
# Hold a BTC long: TP at $33,000, stop-loss triggers at $28,000
python bot.py oco BTCUSDT SELL 0.01 33000 28000 27800
```

**Arguments:**
| Argument           | Description                          |
|--------------------|--------------------------------------|
| `SYMBOL`           | Trading pair                         |
| `SIDE`             | SELL (to exit a long) / BUY (short)  |
| `QUANTITY`         | Quantity per leg                     |
| `TAKE_PROFIT`      | Take-profit limit price              |
| `STOP_PRICE`       | Stop trigger price                   |
| `STOP_LIMIT_PRICE` | Limit price on the stop leg          |

**How It Works (SELL OCO):**
```
TP Limit (SELL) @ $33,000 ──┐
                             ├─ One fills → other cancels
SL Stop-Limit (SELL) @ $28,000/$27,800 ─┘
```

> 📝 **Note:** Binance Futures doesn't natively support OCO. This bot implements
> it by placing both orders independently and running a background monitor thread
> that cancels the surviving order when one fills.

---

### TWAP Strategy *(Advanced)*

Splits a large order into equal child orders over time to minimize price impact.

```bash
# Buy 1.0 BTC total: 10 child orders of 0.1 BTC each, every 60 seconds
python bot.py twap BTCUSDT BUY 1.0 10 60

# Sell 5 ETH total: 5 child orders of 1 ETH each, every 30 seconds
python bot.py twap ETHUSDT SELL 5.0 5 30
```

**Arguments:**
| Argument          | Description                            |
|-------------------|----------------------------------------|
| `SYMBOL`          | Trading pair                           |
| `SIDE`            | BUY or SELL                            |
| `TOTAL_QUANTITY`  | Total amount to execute                |
| `INTERVALS`       | Number of child orders (minimum 2)     |
| `INTERVAL_SECS`   | Seconds between each child order       |

**Output Summary:**
```json
{
  "symbol": "BTCUSDT",
  "side": "BUY",
  "total_quantity": 1.0,
  "intervals": 10,
  "executed_qty": 1.0,
  "average_fill_price": 30124.55,
  "failed_intervals": 0,
  "fill_prices": [30100, 30110, ..., 30150]
}
```

---

### Grid Trading Strategy *(Advanced)*

Automates buy-low/sell-high within a price range using a grid of limit orders.

```bash
# BTC grid: range $28,000–$32,000, 5 grids, 0.001 BTC per level
python bot.py grid BTCUSDT 28000 32000 5 0.001
```

**Arguments:**
| Argument          | Description                            |
|-------------------|----------------------------------------|
| `SYMBOL`          | Trading pair                           |
| `LOWER_PRICE`     | Bottom of the grid range               |
| `UPPER_PRICE`     | Top of the grid range                  |
| `GRIDS`           | Number of grid intervals (minimum 2)   |
| `QTY_PER_GRID`    | Quantity per individual grid order     |

**How It Works:**
```
Price = $30,000  (current)

Grid levels: $28,000 / $28,800 / $29,600 / $30,400 / $31,200 / $32,000
                                                  ↑ current price
BUY orders:  $28,000  $28,800  $29,600  $30,400
SELL orders:                             $30,400  $31,200  $32,000

→ BUY fills at $29,600 → SELL placed at $30,400
→ SELL fills at $30,400 → BUY placed at $29,600
→ Repeat. Profit per cycle: $800 × 0.001 = $0.80 USDT
```

Press **Ctrl+C** to stop the grid. All open orders will be cancelled.

---

## Logging

All actions are logged to **`bot.log`** in the project root.

**Log format:**
```
2024-05-01 14:32:01 | INFO     | market_orders | Placing MARKET BUY order | Symbol: BTCUSDT | Qty: 0.01
2024-05-01 14:32:01 | INFO     | client        | Connecting to Binance Futures TESTNET.
2024-05-01 14:32:02 | INFO     | market_orders | Market order placed successfully | OrderID: 123456789 | Status: FILLED | AvgPrice: 29850.0 | FilledQty: 0.01
```

**Severity levels used:**
| Level    | When used                                              |
|----------|--------------------------------------------------------|
| DEBUG    | Internal state, price checks, poll intervals           |
| INFO     | Successful placements, fills, status updates           |
| WARNING  | Partial fills, graceful stops, rollback notices        |
| ERROR    | Failed API calls, validation failures                  |
| CRITICAL | Unhandled exceptions, rollback failures                |

---

## Validation Rules

| Field            | Rule                                              |
|------------------|---------------------------------------------------|
| Symbol           | Non-empty, alphabetic characters only             |
| Side             | Must be exactly `BUY` or `SELL`                   |
| Quantity         | Must be > 0                                       |
| Price            | Must be > 0                                       |
| Stop-Limit SELL  | `stop_price > limit_price`                        |
| Stop-Limit BUY   | `stop_price < limit_price`                        |
| OCO SELL         | `take_profit > stop_price > stop_limit_price`     |
| Grid             | `lower < upper`, grids ≥ 2, qty > 0               |
| TWAP             | qty > 0, intervals ≥ 2, interval_seconds ≥ 1      |

---

## Environment Variables Reference

| Variable             | Description                         | Default  |
|----------------------|-------------------------------------|----------|
| `BINANCE_API_KEY`    | Your Binance API key                | (required)|
| `BINANCE_API_SECRET` | Your Binance API secret             | (required)|
| `BINANCE_TESTNET`    | `"true"` for testnet, `"false"` live| `"true"` |

---

## Safety Notes

1. **Always test on the testnet first** (`BINANCE_TESTNET=true`).
2. Grid and OCO strategies place **multiple orders simultaneously** — verify
   your account has sufficient margin.
3. TWAP runs for `intervals × interval_seconds` seconds total. Use Ctrl+C
   to abort early; already-placed child orders will remain open.
4. OCO requires the monitor thread to be running to cancel the surviving leg.
   If your process exits, cancel orders manually on Binance.

---

## Resources

- [Binance Futures API Docs](https://binance-docs.github.io/apidocs/futures/en/)
- [Binance Futures Testnet](https://testnet.binancefuture.com/)
- [python-binance-futures-connector](https://github.com/binance/binance-futures-connector-python)
