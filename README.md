# Binance Futures Trading Bot

A CLI-based algorithmic trading bot for Binance USDT-M Futures Demo
with Market, Limit, Stop-Limit, OCO, TWAP, and Grid order support.
Includes structured logging, input validation, and a full web UI.

---

## Project Structure

binance-bot/
├── bot.py
├── requirements.txt
├── .env.example
├── bot.log
├── README.md
├── src/
│   ├── client.py
│   ├── logger.py
│   ├── validator.py
│   ├── market_orders.py
│   ├── limit_orders.py
│   └── advanced/
│       ├── stop_limit.py
│       ├── oco.py
│       ├── twap.py
│       └── grid_strategy.py
├── backend/
│   ├── main.py
│   └── routes/
│       ├── orders.py
│       ├── strategies.py
│       └── websocket.py
└── frontend/
    ├── index.html
    ├── orders.html
    ├── strategies.html
    ├── logs.html
    ├── css/
    │   ├── main.css
    │   └── components.css
    └── js/
        ├── api.js
        ├── chart.js
        ├── logs.js
        └── orders.js

---

## Setup

1. Clone the repository

git clone https://github.com/rishirajdas05/binance-bot.git
cd binance-bot

2. Create virtual environment

python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # Mac/Linux

3. Install dependencies

pip install -r requirements.txt

4. Get API Keys

- Go to demo.binance.com
- Login → Account → API Management
- Create API → Enable Futures
- Copy API Key and Secret Key

5. Create .env file

BINANCE_API_KEY=your_api_key_here
BINANCE_API_SECRET=your_api_secret_here

---

## How to Run (CLI)

Market Order:
    python bot.py market BTCUSDT BUY 0.01
    python bot.py market ETHUSDT SELL 0.5

Limit Order:
    python bot.py limit BTCUSDT BUY 0.01 75000
    python bot.py limit BTCUSDT SELL 0.01 90000 GTC

Stop-Limit Order (Bonus):
    python bot.py stop BTCUSDT SELL 0.01 76000 75000
    python bot.py stop BTCUSDT BUY  0.01 77000 77500

OCO Order (Bonus):
    python bot.py oco BTCUSDT SELL 0.01 90000 74000 73500

TWAP Strategy (Bonus):
    python bot.py twap BTCUSDT BUY 0.05 5 10

Grid Strategy (Bonus):
    python bot.py grid BTCUSDT 74000 80000 5 0.001

---

## Web UI (Bonus)

Install additional dependencies:
    pip install fastapi uvicorn websockets python-multipart

Run the server:
    uvicorn backend.main:app --reload --port 8000

Open browser at: http://localhost:8000

UI Features:
- Live BTC price chart via WebSocket (updates every second)
- Place all order types via forms (Market, Limit, Stop-Limit, OCO)
- View all open orders in real time
- Run and stop TWAP and Grid strategies
- Live log viewer with level filtering (INFO/WARNING/ERROR/CRITICAL)
- Account balance and unrealized PnL display

---

## CLI Output Example

Market Order:
    2026-04-21 13:38:41 [INFO] market_orders: Placing MARKET BUY | Symbol: BTCUSDT | Qty: 0.01
    2026-04-21 13:38:43 [INFO] market_orders: Market order filled | OrderID: 13056934507 | Status: NEW

Limit Order:
    2026-04-21 13:38:48 [INFO] limit_orders: Placing LIMIT BUY | Symbol: BTCUSDT | Price: 75000.0
    2026-04-21 13:38:51 [INFO] limit_orders: Limit order placed | OrderID: 13056934735 | Status: NEW

---

## Validation Rules

Symbol          : Non-empty, letters only (e.g. BTCUSDT)
Side            : Must be BUY or SELL
Quantity        : Must be > 0
Price           : Must be > 0 (required for LIMIT)
Stop-Limit SELL : stop_price > limit_price
Stop-Limit BUY  : stop_price < limit_price
OCO SELL        : take_profit > stop_price > stop_limit_price
Grid            : lower_price < upper_price, grids >= 2
TWAP            : intervals >= 2, interval_seconds >= 1

---

## Logging

All actions logged to bot.log:

    2026-04-21 13:38:41 | INFO     | market_orders | Placing MARKET BUY order
    2026-04-21 13:38:43 | INFO     | client        | Order response: {orderId: 13056934507}
    2026-04-21 13:38:43 | ERROR    | market_orders | Order FAILED | Error: ...

Log levels:
    DEBUG    - Input validation, price polling
    INFO     - Successful orders, fills, status updates
    WARNING  - Partial fills, graceful stops
    ERROR    - Failed API calls, validation errors
    CRITICAL - Fatal errors, unhandled exceptions

---

## Requirements

- Python 3.10+
- Binance Demo account
- Internet connection

---

## Assumptions

- All orders placed on Binance USDT-M Futures Demo environment
- Stop-Limit and OCO stop legs simulated via price polling
  (Demo environment does not support native STOP order type)
- Quantities must meet Binance minimum notional requirements
- Demo and Testnet use separate API keys and URLs

---

## Dependencies

requests>=2.31.0
colorlog>=6.8.0
python-dotenv>=1.0.0
fastapi>=0.110.0
uvicorn[standard]>=0.29.0
websockets>=12.0
python-multipart>=0.0.9

---

## Author

Rishi Raj Das
GitHub: https://github.com/rishirajdas05