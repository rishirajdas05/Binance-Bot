// api.js — All fetch calls to FastAPI backend
// API keys are stored in .env on the server — not needed in frontend

const API_BASE = "http://localhost:8000/api";

// Generic POST
async function apiPost(endpoint, body = {}) {
    const res = await fetch(`${API_BASE}${endpoint}`, {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify(body),
    });
    return res.json();
}

// Generic GET
async function apiGet(endpoint, params = {}) {
    const qs  = new URLSearchParams(params).toString();
    const url = qs ? `${API_BASE}${endpoint}?${qs}` : `${API_BASE}${endpoint}`;
    const res = await fetch(url);
    return res.json();
}

// ── Order APIs ─────────────────────────────────────────────────
const API = {
    marketOrder: (symbol, side, quantity) =>
        apiPost("/orders/market", { symbol, side, quantity }),

    limitOrder: (symbol, side, quantity, price, time_in_force = "GTC") =>
        apiPost("/orders/limit", { symbol, side, quantity, price, time_in_force }),

    stopOrder: (symbol, side, quantity, stop_price, limit_price) =>
        apiPost("/orders/stop", { symbol, side, quantity, stop_price, limit_price }),

    ocoOrder: (symbol, side, quantity, take_profit_price, stop_price, stop_limit_price) =>
        apiPost("/orders/oco", { symbol, side, quantity, take_profit_price, stop_price, stop_limit_price }),

    openOrders: (symbol) =>
        apiGet(`/orders/open/${symbol}`),

    price: (symbol) =>
        apiGet(`/price/${symbol}`),

    account: () =>
        apiGet("/account"),

    startTWAP: (symbol, side, total_quantity, intervals, interval_seconds) =>
        apiPost("/strategies/twap", { symbol, side, total_quantity, intervals, interval_seconds }),

    stopTWAP:  () => apiPost("/strategies/twap/stop"),
    twapResult:() => apiGet("/strategies/twap/result"),

    startGrid: (symbol, lower_price, upper_price, grids, quantity_per_grid) =>
        apiPost("/strategies/grid", { symbol, lower_price, upper_price, grids, quantity_per_grid }),

    stopGrid:  () => apiPost("/strategies/grid/stop"),
    gridResult:() => apiGet("/strategies/grid/result"),
};

// ── Toast helper ───────────────────────────────────────────────
function showToast(message, type = "success") {
    const t = document.getElementById("toast");
    if (!t) return;
    t.textContent = message;
    t.className   = `toast show ${type}`;
    setTimeout(() => t.className = "toast", 3000);
}

// ── Format number ──────────────────────────────────────────────
function fmt(n, decimals = 2) {
    return parseFloat(n).toLocaleString("en-US", {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals,
    });
}