"""Local browser UI for generating PocketOption signals through the hosted API."""

from __future__ import annotations

import json
import socket
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, Tuple

from pocket_signal_client import ApiClient, ApiError, DEFAULT_API_URL
from signal_engine import generate_signal


NOT_CONNECTED_TEXT = "Não conectado. Use /api/connect"


HTML = r"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Pocket Signal Studio</title>
  <style>
    :root {
      color-scheme: dark;
      --bg: #0b1120;
      --panel: #111827;
      --panel-2: #0f172a;
      --text: #f8fafc;
      --muted: #94a3b8;
      --line: #243044;
      --blue: #2563eb;
      --blue-2: #1d4ed8;
      --green: #22c55e;
      --red: #f43f5e;
      --amber: #f59e0b;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font-family: "Segoe UI", Arial, sans-serif;
      letter-spacing: 0;
    }
    main { max-width: 1220px; margin: 0 auto; padding: 24px; }
    header { display: flex; justify-content: space-between; gap: 16px; align-items: flex-end; margin-bottom: 20px; }
    h1 { margin: 0; font-size: 30px; line-height: 1.1; }
    .sub { color: var(--muted); margin-top: 6px; font-size: 14px; }
    .grid { display: grid; grid-template-columns: minmax(0, 1.35fr) minmax(340px, .85fr); gap: 16px; }
    section {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 18px;
      margin-bottom: 16px;
    }
    h2 { margin: 0 0 14px; font-size: 15px; color: #e5e7eb; }
    label { display: block; color: var(--muted); font-size: 12px; margin: 0 0 6px; }
    input, select {
      width: 100%;
      background: #020617;
      border: 1px solid #263247;
      color: var(--text);
      border-radius: 6px;
      padding: 10px 11px;
      font-size: 14px;
      outline: none;
    }
    input:focus, select:focus { border-color: var(--blue); }
    .row { display: grid; grid-template-columns: repeat(12, 1fr); gap: 12px; align-items: end; }
    .c12 { grid-column: span 12; }
    .c6 { grid-column: span 6; }
    .c4 { grid-column: span 4; }
    .c3 { grid-column: span 3; }
    button {
      border: 0;
      border-radius: 6px;
      background: var(--blue);
      color: white;
      font-weight: 700;
      padding: 11px 14px;
      cursor: pointer;
      font-size: 14px;
      min-height: 40px;
    }
    button:hover { background: var(--blue-2); }
    button.secondary { background: #334155; }
    button.secondary:hover { background: #475569; }
    button.danger { background: #be123c; }
    button.danger:hover { background: #9f1239; }
    .pill {
      display: inline-flex;
      align-items: center;
      min-height: 32px;
      padding: 7px 11px;
      border-radius: 999px;
      background: #020617;
      border: 1px solid var(--line);
      color: var(--muted);
      font-size: 13px;
    }
    .signal {
      min-height: 230px;
      display: grid;
      align-content: center;
      border: 1px solid var(--line);
      background: var(--panel-2);
      border-radius: 8px;
      padding: 24px;
      margin-top: 12px;
    }
    .signal .direction { font-size: 56px; font-weight: 800; line-height: 1; }
    .signal .confidence { font-size: 18px; margin-top: 10px; color: var(--muted); }
    .call { color: var(--green); }
    .put { color: var(--red); }
    .wait { color: var(--amber); }
    .metrics { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-top: 14px; }
    .metric { background: #020617; border: 1px solid var(--line); border-radius: 8px; padding: 12px; }
    .metric span { color: var(--muted); font-size: 12px; }
    .metric strong { display: block; margin-top: 5px; font-size: 17px; }
    ul { margin: 12px 0 0; padding-left: 18px; color: #cbd5e1; }
    li { margin: 6px 0; }
    pre {
      white-space: pre-wrap;
      word-break: break-word;
      background: #020617;
      border: 1px solid var(--line);
      border-radius: 8px;
      color: #cbd5e1;
      padding: 12px;
      min-height: 220px;
      max-height: 420px;
      overflow: auto;
      font-size: 12px;
      margin: 0;
    }
    .actions { display: flex; gap: 10px; flex-wrap: wrap; }
    @media (max-width: 920px) {
      .grid { grid-template-columns: 1fr; }
      .c6, .c4, .c3 { grid-column: span 12; }
      header { display: block; }
    }
  </style>
</head>
<body>
<main>
  <header>
    <div>
      <h1>Pocket Signal Studio</h1>
      <div class="sub">Gerador de sinais via API Railway. Sem grafico, foco em decisao e execucao.</div>
    </div>
    <div class="pill" id="status">Carregando...</div>
  </header>

  <div class="grid">
    <div>
      <section>
        <h2>Sessao</h2>
        <div class="row">
          <div class="c12">
            <label>Timeout da API em segundos</label>
            <input id="apiTimeout" type="number" value="240" min="20" max="300" />
          </div>
          <div class="c12">
            <label>SSID completo</label>
            <input id="ssid" type="password" placeholder='42["auth",{"session":"..."}]' />
          </div>
          <div class="c12">
            <label>WebSocket URL opcional</label>
            <input id="websocketUrl" placeholder="wss://demo-api-eu.po.market/socket.io/?EIO=4&transport=websocket" />
          </div>
          <div class="c12 actions">
            <button onclick="connectSession()">Conectar</button>
            <button class="secondary" onclick="loadBalance()">Saldo</button>
            <button class="secondary" onclick="loadDiagnostics()">Diagnostico</button>
          </div>
        </div>
      </section>

      <section>
        <h2>Gerar sinal</h2>
        <div class="row">
          <div class="c4">
            <label>Ativo</label>
            <select id="asset">
              <option>EURUSD_otc</option><option>GBPUSD_otc</option><option>USDJPY_otc</option>
              <option>AUDUSD_otc</option><option>USDCAD_otc</option><option>USDCHF_otc</option>
              <option>EURJPY_otc</option><option>GBPJPY_otc</option><option>BTCUSD_otc</option>
            </select>
          </div>
          <div class="c3">
            <label>Timeframe</label>
            <select id="timeframe"><option value="30">30s</option><option value="60" selected>60s</option><option value="120">120s</option><option value="300">300s</option></select>
          </div>
          <div class="c3">
            <label>Candles</label>
            <input id="count" type="number" value="100" min="30" max="300" />
          </div>
          <div class="c2">
            <label>Min conf.</label>
            <input id="minConfidence" type="number" value="62" min="50" max="90" />
          </div>
          <div class="c12">
            <button onclick="generateSignal()">Gerar Sinal</button>
          </div>
        </div>
        <div class="signal">
          <div id="direction" class="direction wait">AGUARDAR</div>
          <div id="summary" class="confidence">Conecte a sessao e gere um sinal.</div>
          <div class="metrics">
            <div class="metric"><span>Preco</span><strong id="price">-</strong></div>
            <div class="metric"><span>Payout</span><strong id="payout">-</strong></div>
            <div class="metric"><span>RSI</span><strong id="rsi">-</strong></div>
          </div>
          <ul id="reasons"><li>As confluencias aparecem aqui.</li></ul>
        </div>
      </section>
    </div>

    <div>
      <section>
        <h2>Execucao opcional</h2>
        <div class="row">
          <div class="c6">
            <label>Valor</label>
            <input id="amount" type="number" value="1" min="1" step="1" />
          </div>
          <div class="c6">
            <label>Duracao</label>
            <select id="duration"><option value="30">30s</option><option value="60" selected>60s</option><option value="120">120s</option><option value="300">300s</option></select>
          </div>
          <div class="c12 actions">
            <button class="danger" onclick="sendOrder()">Enviar Sinal</button>
            <button class="secondary" onclick="waitResult()">Aguardar Resultado</button>
          </div>
        </div>
        <p class="sub" id="orderStatus">Nenhuma ordem enviada.</p>
      </section>
      <section>
        <h2>Retorno da API</h2>
        <pre id="log">Pronto.</pre>
      </section>
    </div>
  </div>
</main>
<script>
let lastSignal = null;
let lastOrderId = null;

function apiPayload(extra = {}) {
  return {
    api_timeout: Number(document.getElementById("apiTimeout").value || 240),
    ...extra
  };
}
function setStatus(text) { document.getElementById("status").textContent = text; }
function log(title, data) { document.getElementById("log").textContent = `== ${title} ==\n` + JSON.stringify(data, null, 2); }
async function post(path, body) {
  setStatus("Processando...");
  const res = await fetch(path, { method: "POST", headers: {"Content-Type":"application/json"}, body: JSON.stringify(body) });
  const data = await res.json();
  setStatus(res.ok ? "Pronto" : "Erro");
  if (!res.ok) throw data;
  return data;
}
async function connectSession() {
  try {
    clearSessionState();
    const data = await post("/connect", apiPayload({
      ssid: document.getElementById("ssid").value.trim(),
      websocket_url: document.getElementById("websocketUrl").value.trim()
    }));
    log("init", data);
    await loadBalance();
  } catch (e) { log("erro", e); }
}
async function loadBalance() {
  try { log("balance", await post("/balance", apiPayload())); } catch (e) { log("erro", e); }
}
async function loadDiagnostics() {
  try { log("diagnostics", await post("/diagnostics", apiPayload())); } catch (e) { log("erro", e); }
}
async function generateSignal() {
  try {
    const data = await post("/signal", apiPayload({
      asset: document.getElementById("asset").value,
      timeframe: Number(document.getElementById("timeframe").value),
      count: Number(document.getElementById("count").value),
      min_confidence: Number(document.getElementById("minConfidence").value)
    }));
    lastSignal = data.signal;
    const direction = document.getElementById("direction");
    direction.textContent = data.signal.direction;
    direction.className = "direction " + (data.signal.direction === "CALL" ? "call" : data.signal.direction === "PUT" ? "put" : "wait");
    document.getElementById("summary").textContent = data.signal.summary;
    document.getElementById("price").textContent = fmt(data.signal.stats.price);
    document.getElementById("payout").textContent = fmt(data.signal.stats.payout, "%");
    document.getElementById("rsi").textContent = fmt(data.signal.stats.rsi_14);
    document.getElementById("reasons").innerHTML = data.signal.reasons.map(r => `<li>${escapeHtml(r)}</li>`).join("");
    log("signal", data);
  } catch (e) { log("erro", e); }
}
async function sendOrder() {
  if (!lastSignal || !["CALL","PUT"].includes(lastSignal.direction)) {
    alert("Gere um sinal CALL ou PUT antes de enviar ordem.");
    return;
  }
  if (!confirm(`Enviar ${lastSignal.direction}?`)) return;
  try {
    const data = await post("/order", apiPayload({
      asset: document.getElementById("asset").value,
      direction: lastSignal.direction,
      amount: Number(document.getElementById("amount").value),
      duration_seconds: Number(document.getElementById("duration").value)
    }));
    lastOrderId = data.request_id;
    document.getElementById("orderStatus").textContent = "Ordem enviada: " + (lastOrderId || "-");
    log("order", data);
  } catch (e) { log("erro", e); }
}
async function waitResult() {
  if (!lastOrderId) { alert("Envie uma ordem antes."); return; }
  try {
    const data = await post("/result", apiPayload({
      request_id: lastOrderId,
      timeout: Math.max(Number(document.getElementById("duration").value) + 90, 180)
    }));
    document.getElementById("orderStatus").textContent = `Resultado: ${data.result} | Lucro: ${data.profit}`;
    log("result", data);
  } catch (e) { log("erro", e); }
}
function fmt(value, suffix = "") {
  if (value === null || value === undefined) return "-";
  if (typeof value === "number") return (Math.abs(value) < 10 && suffix === "" ? value.toFixed(5) : value.toFixed(1)) + suffix;
  return value + suffix;
}
function escapeHtml(text) {
  return String(text).replace(/[&<>"']/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[m]));
}
function clearSessionState() {
  lastSignal = null;
  lastOrderId = null;
  const direction = document.getElementById("direction");
  direction.textContent = "AGUARDAR";
  direction.className = "direction wait";
  document.getElementById("summary").textContent = "Sessao limpa. Conectando novamente...";
  document.getElementById("price").textContent = "-";
  document.getElementById("payout").textContent = "-";
  document.getElementById("rsi").textContent = "-";
  document.getElementById("reasons").innerHTML = "<li>Aguardando nova conexao.</li>";
  document.getElementById("orderStatus").textContent = "Nenhuma ordem enviada.";
}
post("/health", apiPayload()).then(d => { setStatus("API online"); log("health", d); }).catch(e => { setStatus("Erro"); log("erro", e); });
</script>
</body>
</html>"""


def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def json_response(handler: BaseHTTPRequestHandler, status: int, payload: Any) -> None:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def read_json(handler: BaseHTTPRequestHandler) -> Dict[str, Any]:
    length = int(handler.headers.get("Content-Length", "0"))
    if length <= 0:
        return {}
    return json.loads(handler.rfile.read(length).decode("utf-8"))


def api_client(payload: Dict[str, Any]) -> ApiClient:
    timeout = int(payload.get("api_timeout") or 240)
    timeout = max(20, min(timeout, 300))
    return ApiClient(DEFAULT_API_URL, timeout=timeout)


def signal_payload(signal: Any) -> Dict[str, Any]:
    return {
        "direction": signal.direction,
        "confidence": signal.confidence,
        "summary": signal.summary,
        "entry_price": signal.entry_price,
        "reasons": signal.reasons,
        "stats": signal.stats,
    }


def is_not_connected_error(exc: ApiError) -> bool:
    payload = exc.payload
    if not isinstance(payload, dict):
        return False
    detail = payload.get("detail")
    return exc.status == 503 and detail == NOT_CONNECTED_TEXT


def with_reconnect(client: ApiClient, action: Any) -> Any:
    try:
        return action()
    except ApiError as exc:
        if not is_not_connected_error(exc):
            raise
        client.connect()
        return action()


class StudioHandler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args: Any) -> None:
        return

    def do_GET(self) -> None:
        if self.path != "/":
            self.send_error(404)
            return
        body = HTML.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:
        try:
            payload = read_json(self)
            status, data = self.route_post(payload)
            json_response(self, status, data)
        except ApiError as exc:
            json_response(self, exc.status or 502, {"error": str(exc), "payload": exc.payload})
        except Exception as exc:
            json_response(self, 500, {"error": str(exc)})

    def route_post(self, payload: Dict[str, Any]) -> Tuple[int, Any]:
        client = api_client(payload)
        if self.path == "/health":
            return 200, client.health()
        if self.path == "/connect":
            init_data = client.init(
                payload.get("ssid", ""),
                payload.get("websocket_url") or None,
                connect_after_init=False,
            )
            connect_data = client.connect()
            return 200, {"init": init_data, "connect": connect_data}
        if self.path == "/balance":
            return 200, with_reconnect(client, client.balance)
        if self.path == "/diagnostics":
            return 200, client.diagnostics()
        if self.path == "/signal":
            asset = payload.get("asset", "EURUSD_otc")
            payout_data = with_reconnect(client, lambda: client.payout(asset))
            payout = payout_data.get("payout") if isinstance(payout_data, dict) else None
            candles = with_reconnect(
                client,
                lambda: client.candles(
                    asset,
                    int(payload.get("timeframe", 60)),
                    int(payload.get("count", 100)),
                ),
            )
            signal = generate_signal(candles, payout=payout, min_confidence=int(payload.get("min_confidence", 62)))
            return 200, {"signal": signal_payload(signal), "payout": payout_data, "candles": len(candles)}
        if self.path == "/order":
            return 200, with_reconnect(
                client,
                lambda: client.place_order(
                    payload.get("asset", "EURUSD_otc"),
                    payload.get("direction", "CALL"),
                    float(payload.get("amount", 1)),
                    int(payload.get("duration_seconds", 60)),
                ),
            )
        if self.path == "/result":
            return 200, with_reconnect(
                client,
                lambda: client.order_result(payload.get("request_id", ""), int(payload.get("timeout", 180))),
            )
        return 404, {"error": "Rota local nao encontrada"}


def main() -> int:
    port = find_free_port()
    server = ThreadingHTTPServer(("127.0.0.1", port), StudioHandler)
    url = f"http://127.0.0.1:{port}/"
    threading.Timer(0.4, lambda: webbrowser.open(url)).start()
    print(f"Pocket Signal Studio aberto em {url}")
    print("Feche esta janela para encerrar o aplicativo.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
