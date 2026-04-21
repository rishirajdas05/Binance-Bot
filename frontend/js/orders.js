// orders.js — Order form logic

let selectedSide      = "BUY";
let selectedOrderType = "market";

document.addEventListener("DOMContentLoaded", () => {
    // Side selector
    document.querySelectorAll(".side-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".side-btn").forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            selectedSide = btn.dataset.side;
        });
    });

    // Order type tabs
    document.querySelectorAll(".order-tab").forEach(tab => {
        tab.addEventListener("click", () => {
            document.querySelectorAll(".order-tab").forEach(t => t.classList.remove("active"));
            tab.classList.add("active");
            selectedOrderType = tab.dataset.type;
            showOrderForm(selectedOrderType);
        });
    });

    // Submit button
    const submitBtn = document.getElementById("submit-order");
    if (submitBtn) submitBtn.addEventListener("click", submitOrder);

    // Load saved credentials
    const keyInput    = document.getElementById("api-key-input");
    const secretInput = document.getElementById("api-secret-input");
    if (keyInput)    keyInput.value    = localStorage.getItem("api_key")    || "";
    if (secretInput) secretInput.value = localStorage.getItem("api_secret") || "";

    // Save creds on input
    if (keyInput)    keyInput.addEventListener("input",    () => saveCreds(keyInput.value, secretInput?.value));
    if (secretInput) secretInput.addEventListener("input", () => saveCreds(keyInput?.value, secretInput.value));

    showOrderForm("market");
    loadOpenOrders();
});

function showOrderForm(type) {
    document.querySelectorAll(".order-form").forEach(f => f.style.display = "none");
    const form = document.getElementById(`form-${type}`);
    if (form) form.style.display = "block";
}

async function submitOrder() {
    const symbol = document.getElementById("symbol")?.value?.toUpperCase() || "BTCUSDT";
    const btn    = document.getElementById("submit-order");
    btn.textContent = "Placing...";
    btn.disabled    = true;

    try {
        let result;

        if (selectedOrderType === "market") {
            const qty = parseFloat(document.getElementById("qty-market").value);
            result    = await API.marketOrder(symbol, selectedSide, qty);

        } else if (selectedOrderType === "limit") {
            const qty   = parseFloat(document.getElementById("qty-limit").value);
            const price = parseFloat(document.getElementById("price-limit").value);
            const tif   = document.getElementById("tif-limit").value;
            result      = await API.limitOrder(symbol, selectedSide, qty, price, tif);

        } else if (selectedOrderType === "stop") {
            const qty   = parseFloat(document.getElementById("qty-stop").value);
            const stop  = parseFloat(document.getElementById("stop-price").value);
            const limit = parseFloat(document.getElementById("limit-price-stop").value);
            result      = await API.stopOrder(symbol, selectedSide, qty, stop, limit);

        } else if (selectedOrderType === "oco") {
            const qty   = parseFloat(document.getElementById("qty-oco").value);
            const tp    = parseFloat(document.getElementById("tp-price").value);
            const stop  = parseFloat(document.getElementById("stop-price-oco").value);
            const sl    = parseFloat(document.getElementById("sl-price").value);
            result      = await API.ocoOrder(symbol, selectedSide, qty, tp, stop, sl);
        }

        if (result?.success) {
            showToast(`Order placed! ID: ${result.order?.orderId || result.order?.take_profit_order?.orderId}`, "success");
            loadOpenOrders();
        } else {
            showToast(`Error: ${result?.detail || "Unknown error"}`, "error");
        }

    } catch (e) {
        showToast(`Failed: ${e.message}`, "error");
    } finally {
        btn.textContent = "Place Order";
        btn.disabled    = false;
    }
}

async function loadOpenOrders() {
    const symbol = document.getElementById("symbol")?.value?.toUpperCase() || "BTCUSDT";
    try {
        const result = await API.openOrders(symbol);
        const tbody  = document.getElementById("open-orders-body");
        if (!tbody) return;

        const orders = result.orders || [];
        if (orders.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6" class="text-muted" style="text-align:center;padding:20px">No open orders</td></tr>`;
            return;
        }

        tbody.innerHTML = orders.map(o => `
            <tr>
                <td>${o.orderId}</td>
                <td>${o.symbol}</td>
                <td class="${o.side === 'BUY' ? 'text-green' : 'text-red'}">${o.side}</td>
                <td>${o.type}</td>
                <td>${fmt(o.price)}</td>
                <td><span class="badge badge-yellow">${o.status}</span></td>
            </tr>
        `).join("");
    } catch (e) {
        console.error("Failed to load open orders", e);
    }
}