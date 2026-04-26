// logs.js — Live log viewer

let logSocket  = null;
let autoScroll = true;

document.addEventListener("DOMContentLoaded", () => {
    connectLogSocket();

    const clearBtn = document.getElementById("clear-logs");
    if (clearBtn) clearBtn.addEventListener("click", () => {
        const box = document.getElementById("log-box");
        if (box) box.innerHTML = "";
    });

    const scrollBtn = document.getElementById("toggle-scroll");
    if (scrollBtn) scrollBtn.addEventListener("click", () => {
        autoScroll = !autoScroll;
        scrollBtn.textContent = autoScroll ? "Auto-scroll ON" : "Auto-scroll OFF";
    });
});

function connectLogSocket() {
    const wsUrl = window.location.hostname === "localhost"
        ? "ws://localhost:8000/ws/logs"
        : "wss://binance-bot-gwbg.onrender.com/ws/logs";

    logSocket = new WebSocket(wsUrl);

    logSocket.onmessage = (event) => {
        appendLog(event.data);
    };

    logSocket.onerror = () => {
        console.warn("Log socket error — retrying in 3s");
        setTimeout(connectLogSocket, 3000);
    };

    logSocket.onclose = () => {
        console.warn("Log socket closed — retrying in 3s");
        setTimeout(connectLogSocket, 3000);
    };
}

function appendLog(line) {
    const box = document.getElementById("log-box");
    if (!box) return;

    const div  = document.createElement("div");
    let level  = "DEBUG";
    if (line.includes("| INFO"))     level = "INFO";
    if (line.includes("| WARNING"))  level = "WARNING";
    if (line.includes("| ERROR"))    level = "ERROR";
    if (line.includes("| CRITICAL")) level = "CRITICAL";

    div.className   = `log-line ${level}`;
    div.textContent = line;
    box.appendChild(div);

    if (autoScroll) box.scrollTop = box.scrollHeight;

    while (box.children.length > 500) box.removeChild(box.firstChild);
}