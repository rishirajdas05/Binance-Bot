// chart.js — Live price chart using Chart.js

let priceChart   = null;
let priceLabels  = [];
let priceData    = [];
let priceSocket  = null;
const MAX_POINTS = 60;

function initChart(symbol = "BTCUSDT") {
    const ctx = document.getElementById("price-chart");
    if (!ctx) return;

    if (priceChart) priceChart.destroy();

    priceChart = new Chart(ctx, {
        type: "line",
        data: {
            labels:   priceLabels,
            datasets: [{
                label:           `${symbol} Mark Price`,
                data:            priceData,
                borderColor:     "#f0b90b",
                backgroundColor: "rgba(240,185,11,0.05)",
                borderWidth:     2,
                pointRadius:     0,
                tension:         0.3,
                fill:            true,
            }]
        },
        options: {
            responsive:          true,
            maintainAspectRatio: false,
            animation:           false,
            scales: {
                x: {
                    ticks: { color: "#848e9c", maxTicksLimit: 8 },
                    grid:  { color: "#2b3139" },
                },
                y: {
                    ticks: { color: "#848e9c", callback: v => "$" + v.toLocaleString() },
                    grid:  { color: "#2b3139" },
                }
            },
            plugins: {
                legend: { labels: { color: "#eaecef" } },
            }
        }
    });
}

function connectPriceSocket(symbol = "BTCUSDT") {
    if (priceSocket) priceSocket.close();

    priceSocket = new WebSocket(`wss://binance-bot-gwbg.onrender.com/ws/price/${symbol}`);

    priceSocket.onmessage = (event) => {
        const data  = JSON.parse(event.data);
        const price = data.price;
        const now   = new Date().toLocaleTimeString();

        // Update price display
        const display = document.getElementById("live-price");
        if (display) {
            const prev = parseFloat(display.dataset.prev || price);
            display.textContent     = "$" + fmt(price);
            display.dataset.prev    = price;
            display.style.color     = price >= prev ? "#0ecb81" : "#f6465d";
        }

        // Update chart
        priceLabels.push(now);
        priceData.push(price);

        if (priceLabels.length > MAX_POINTS) {
            priceLabels.shift();
            priceData.shift();
        }

        if (priceChart) priceChart.update();
    };

    priceSocket.onerror = () => {
        console.warn("WebSocket error — retrying in 3s");
        setTimeout(() => connectPriceSocket(symbol), 3000);
    };
}