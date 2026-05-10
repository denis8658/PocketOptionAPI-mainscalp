"""
Standalone REST client for the PocketOption API server.

This program is intentionally separate from the WebSocket API implementation.
It talks only to the hosted REST API and can be packaged as a Windows .exe.
"""

from __future__ import annotations

import argparse
import json
import os
import socket
import sys
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


DEFAULT_API_URL = "https://pocketoptionapi-mainscalp-production-0434.up.railway.app"
DEFAULT_TIMEOUT = 240


class ApiError(RuntimeError):
    """Raised when the REST API returns an error."""

    def __init__(self, status: Optional[int], payload: Any):
        self.status = status
        self.payload = payload
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        if isinstance(self.payload, dict):
            detail = self.payload.get("detail", self.payload)
            if isinstance(detail, dict):
                message = detail.get("message")
                failure_type = detail.get("diagnostics", {}).get("failure_type")
                if message and failure_type:
                    return f"HTTP {self.status}: {message} ({failure_type})"
                if message:
                    return f"HTTP {self.status}: {message}"
            return f"HTTP {self.status}: {json.dumps(self.payload, ensure_ascii=False)}"
        return f"HTTP {self.status}: {self.payload}"


@dataclass
class ApiClient:
    """Small stdlib-only HTTP client for the hosted API."""

    base_url: str = DEFAULT_API_URL
    timeout: int = DEFAULT_TIMEOUT

    def __post_init__(self) -> None:
        self.base_url = self.base_url.rstrip("/")

    def request(
        self,
        method: str,
        path: str,
        payload: Optional[Dict[str, Any]] = None,
        query: Optional[Dict[str, Any]] = None,
    ) -> Any:
        url = f"{self.base_url}{path}"
        if query:
            url = f"{url}?{urlencode(query)}"

        body = None
        headers = {"Accept": "application/json"}
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"

        req = Request(url, data=body, headers=headers, method=method.upper())
        try:
            with urlopen(req, timeout=self.timeout) as response:
                raw = response.read().decode("utf-8")
                return json.loads(raw) if raw else None
        except HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace")
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                payload = raw
            raise ApiError(exc.code, payload) from exc
        except URLError as exc:
            raise ApiError(None, f"Network error: {exc}") from exc
        except (TimeoutError, socket.timeout) as exc:
            raise ApiError(
                None,
                "Timeout aguardando resposta da API. Tente novamente ou aumente o timeout.",
            ) from exc

    def disconnect(self) -> Any:
        return self.request("POST", "/api/disconnect")

    def connect(self) -> Any:
        return self.request("POST", "/api/connect")

    def init(
        self,
        ssid: str,
        websocket_url: Optional[str] = None,
        disconnect_first: bool = True,
        connect_after_init: bool = True,
    ) -> Any:
        if disconnect_first:
            try:
                self.disconnect()
            except ApiError:
                pass

        payload: Dict[str, Any] = {"ssid": ssid, "connect_after_init": connect_after_init}
        if websocket_url:
            payload["websocket_url"] = websocket_url
        return self.request("POST", "/api/init", payload)

    def health(self) -> Any:
        return self.request("GET", "/health")

    def diagnostics(self) -> Any:
        return self.request("GET", "/api/diagnostics")

    def balance(self) -> Any:
        return self.request("GET", "/api/balance")

    def payout(self, asset: str) -> Any:
        return self.request("GET", f"/api/payouts/{asset}")

    def candles(self, asset: str, timeframe: int, count: int) -> Any:
        return self.request(
            "POST",
            "/api/candles",
            {"asset": asset, "timeframe": timeframe, "count": count},
        )

    def place_order(
        self,
        asset: str,
        direction: str,
        amount: float,
        duration_seconds: int,
    ) -> Any:
        return self.request(
            "POST",
            "/api/order/place",
            {
                "asset": asset,
                "direction": direction.upper(),
                "amount": amount,
                "duration_seconds": duration_seconds,
            },
        )

    def order_result(self, request_id: str, timeout: int = 180) -> Any:
        return self.request("GET", f"/api/order/result/{request_id}", query={"timeout": timeout})


def print_json(title: str, data: Any) -> None:
    print(f"\n== {title} ==")
    print(json.dumps(data, indent=2, ensure_ascii=False))


def read_required(prompt: str) -> str:
    while True:
        value = input(prompt).strip()
        if value:
            return value


def read_optional(prompt: str) -> Optional[str]:
    value = input(prompt).strip()
    return value or None


def interactive(args: argparse.Namespace) -> int:
    client = ApiClient(args.api_url, args.timeout)

    ssid = args.ssid or os.getenv("PO_SSID") or read_required("SSID completo: ")
    websocket_url = args.websocket_url or os.getenv("PO_WEBSOCKET_URL") or read_optional(
        "WebSocket URL opcional: "
    )

    try:
        print_json("init", client.init(ssid, websocket_url))
        print_json("health", client.health())
        print_json("diagnostics", client.diagnostics())
        print_json("balance", client.balance())
    except ApiError as exc:
        print(f"\nFalha ao inicializar: {exc}", file=sys.stderr)
        if isinstance(exc.payload, dict):
            print(json.dumps(exc.payload, indent=2, ensure_ascii=False), file=sys.stderr)
        return 1

    while True:
        print("\nComandos:")
        print("1 - Ver saldo")
        print("2 - Ver payout")
        print("3 - Buscar candles")
        print("4 - Enviar ordem manual")
        print("5 - Diagnostico")
        print("0 - Sair")
        choice = input("> ").strip()

        try:
            if choice == "1":
                print_json("balance", client.balance())
            elif choice == "2":
                asset = read_required("Ativo (ex: EURUSD_otc): ")
                print_json("payout", client.payout(asset))
            elif choice == "3":
                asset = read_required("Ativo (ex: EURUSD_otc): ")
                timeframe = int(read_required("Timeframe em segundos (ex: 60): "))
                count = int(read_required("Quantidade (ex: 100): "))
                print_json("candles", client.candles(asset, timeframe, count))
            elif choice == "4":
                asset = read_required("Ativo (ex: EURUSD_otc): ")
                direction = read_required("Direcao CALL/PUT: ").upper()
                amount = float(read_required("Valor: ").replace(",", "."))
                duration = int(read_required("Duracao em segundos: "))
                order = client.place_order(asset, direction, amount, duration)
                print_json("order", order)

                request_id = order.get("request_id") if isinstance(order, dict) else None
                if request_id and input("Aguardar resultado? [s/N] ").strip().lower() == "s":
                    wait_timeout = max(duration + 90, 180)
                    print_json("result", client.order_result(request_id, wait_timeout))
            elif choice == "5":
                print_json("diagnostics", client.diagnostics())
            elif choice == "0":
                return 0
            else:
                print("Comando invalido.")
        except (ApiError, ValueError) as exc:
            print(f"Erro: {exc}", file=sys.stderr)


def command_mode(args: argparse.Namespace) -> int:
    client = ApiClient(args.api_url, args.timeout)
    try:
        if args.command == "health":
            print_json("health", client.health())
        elif args.command == "init":
            ssid = args.ssid or os.getenv("PO_SSID") or read_required("SSID completo: ")
            websocket_url = args.websocket_url or os.getenv("PO_WEBSOCKET_URL")
            print_json("init", client.init(ssid, websocket_url))
        elif args.command == "balance":
            print_json("balance", client.balance())
        elif args.command == "diagnostics":
            print_json("diagnostics", client.diagnostics())
        elif args.command == "payout":
            print_json("payout", client.payout(args.asset))
        elif args.command == "candles":
            print_json("candles", client.candles(args.asset, args.timeframe, args.count))
        elif args.command == "order":
            order = client.place_order(args.asset, args.direction, args.amount, args.duration_seconds)
            print_json("order", order)
            request_id = order.get("request_id") if isinstance(order, dict) else None
            if args.wait and request_id:
                wait_timeout = args.result_timeout or max(args.duration_seconds + 90, 180)
                print_json("result", client.order_result(request_id, wait_timeout))
        else:
            return interactive(args)
    except ApiError as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        if isinstance(exc.payload, dict):
            print(json.dumps(exc.payload, indent=2, ensure_ascii=False), file=sys.stderr)
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Cliente EXE para API PocketOption")
    parser.add_argument(
        "--api-url",
        default=os.getenv("PO_API_URL", DEFAULT_API_URL),
        help=f"URL raiz da API. Padrao: {DEFAULT_API_URL}",
    )
    parser.add_argument("--timeout", type=int, default=int(os.getenv("PO_API_TIMEOUT", DEFAULT_TIMEOUT)))
    parser.add_argument("--ssid", default=os.getenv("PO_SSID"), help="SSID completo 42[\"auth\",...]")
    parser.add_argument("--websocket-url", default=os.getenv("PO_WEBSOCKET_URL"))

    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("interactive")
    subparsers.add_parser("health")
    subparsers.add_parser("diagnostics")
    subparsers.add_parser("balance")
    subparsers.add_parser("init")

    payout = subparsers.add_parser("payout")
    payout.add_argument("asset")

    candles = subparsers.add_parser("candles")
    candles.add_argument("asset")
    candles.add_argument("--timeframe", type=int, default=60)
    candles.add_argument("--count", type=int, default=100)

    order = subparsers.add_parser("order")
    order.add_argument("asset")
    order.add_argument("direction", choices=["CALL", "PUT", "call", "put"])
    order.add_argument("amount", type=float)
    order.add_argument("--duration-seconds", type=int, default=60)
    order.add_argument("--wait", action="store_true")
    order.add_argument("--result-timeout", type=int, default=None)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.command in (None, "interactive"):
        return interactive(args)
    return command_mode(args)


if __name__ == "__main__":
    raise SystemExit(main())
