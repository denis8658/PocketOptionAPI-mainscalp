#!/usr/bin/env python3
"""
🧪 Script de Testes - PocketOption API Railway
Testa todos os endpoints da API após redeploy
"""

import requests
import json
import time
from typing import Dict, Any, Optional

# Configuração
import os

BASE_URL = "https://pocketoptionapi-mainscalp-production-0434.up.railway.app"

# SSID diário (todo dia muda). Preferimos POCKET_OPTION_SSID, e fallback para SSID.
SSID = os.getenv("POCKET_OPTION_SSID") or os.getenv("SSID")

# is_demo opcional para coerência com o SSID.
# Pode setar 0/1 ou true/false. Se não setar, o backend usa default.
IS_DEMO = os.getenv("POCKET_OPTION_IS_DEMO") or os.getenv("IS_DEMO")

# Cores para output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(title: str):
    """Imprime header formatado"""
    print(f"\n{Colors.CYAN}{Colors.BOLD}{'=' * 70}{Colors.END}")
    print(f"{Colors.CYAN}{Colors.BOLD}{title.center(70)}{Colors.END}")
    print(f"{Colors.CYAN}{Colors.BOLD}{'=' * 70}{Colors.END}\n")

def print_test(name: str, status: bool, message: str = ""):
    """Imprime resultado do teste"""
    icon = f"{Colors.GREEN}✓{Colors.END}" if status else f"{Colors.RED}✗{Colors.END}"
    print(f"{icon} {name}")
    if message:
        print(f"  {Colors.YELLOW}→ {message}{Colors.END}")

def test_endpoint(method: str, endpoint: str, **kwargs) -> tuple[bool, Dict[str, Any]]:
    """Testa um endpoint e retorna (sucesso, resposta)"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, timeout=10, **kwargs)
        elif method.upper() == "POST":
            response = requests.post(url, timeout=10, **kwargs)
        else:
            return False, {"error": f"Método {method} não suportado"}
        
        try:
            data = response.json()
        except:
            data = {"text": response.text[:100]}
        
        return response.status_code < 400, {
            "status_code": response.status_code,
            "data": data
        }
    except requests.exceptions.Timeout:
        return False, {"error": "Timeout (>10s)"}
    except requests.exceptions.ConnectionError:
        return False, {"error": "Erro de conexão"}
    except Exception as e:
        return False, {"error": str(e)}

# ==================== TESTES ====================

def test_server_health():
    """Testa saúde do servidor"""
    print_header("1. VERIFICACAO DE SERVIDOR")
    
    # Teste 1: Endpoint raiz
    success, resp = test_endpoint("GET", "/")
    print_test("GET /", success, f"Status {resp.get('status_code', 'N/A')}")
    if success and "name" in resp.get("data", {}):
        print(f"  {Colors.BLUE}→ Servidor: {resp['data']['name']}{Colors.END}")
    
    # Teste 2: Health check
    success, resp = test_endpoint("GET", "/health")
    print_test("GET /health", success, f"Status {resp.get('status_code', 'N/A')}")
    if success:
        data = resp.get("data", {})
        print(f"  {Colors.BLUE}→ Status: {data.get('status', 'N/A')}{Colors.END}")
        print(f"  {Colors.BLUE}→ Conectado: {data.get('connected', 'N/A')}{Colors.END}")

def test_connection():
    """Testa conexão com PocketOption"""
    print_header("2. CONEXAO COM POCKETOPTION")

    if not SSID:
        print_test("POST /api/init", False, "SSID não definido via POCKET_OPTION_SSID/SSID")
        return

    # Teste 1: Inicializar (deve usar o SSID do dia)
    init_payload: Dict[str, Any] = {"ssid": SSID}
    if IS_DEMO is not None and str(IS_DEMO).strip() != "":
        v = str(IS_DEMO).strip().lower()
        if v in ("1", "true", "yes"):
            init_payload["is_demo"] = True
        elif v in ("0", "false", "no"):
            init_payload["is_demo"] = False
        else:
            print_test("POST /api/init", False, f"IS_DEMO inválido: {IS_DEMO} (use 0/1 ou true/false)")
            return

    success, resp = test_endpoint(
        "POST",
        "/api/init",
        json=init_payload
    )
    print_test("POST /api/init", success, f"Status {resp.get('status_code', 'N/A')}")

    if not success:
        return

    # Aguardar um pouco para init/setar cliente
    time.sleep(1)

    # Teste 2: Conectar
    success, resp = test_endpoint("POST", "/api/connect", json={})
    print_test("POST /api/connect", success, f"Status {resp.get('status_code', 'N/A')}")

def test_account_endpoints():
    """Testa endpoints de conta"""
    print_header("3. ENDPOINTS DE CONTA")
    
    # Teste 1: Balance
    success, resp = test_endpoint("GET", "/api/balance")
    print_test("GET /api/balance", success, f"Status {resp.get('status_code', 'N/A')}")
    
    # Teste 2: Connection Stats
    success, resp = test_endpoint("GET", "/api/connection-stats")
    print_test("GET /api/connection-stats", success, f"Status {resp.get('status_code', 'N/A')}")

def test_order_endpoints():
    """Testa endpoints de ordens"""
    print_header("4. ENDPOINTS DE ORDENS")
    
    # Teste 1: Place Order
    success, resp = test_endpoint("POST", "/api/order/place", json={
        "asset": "EURUSD",
        "direction": "CALL",
        "amount": 10,
        "timeframe": 5
    })
    print_test("POST /api/order/place", success, f"Status {resp.get('status_code', 'N/A')}")
    
    # Teste 2: Active Orders
    success, resp = test_endpoint("GET", "/api/orders/active")
    print_test("GET /api/orders/active", success, f"Status {resp.get('status_code', 'N/A')}")

def test_market_endpoints():
    """Testa endpoints de dados de mercado"""
    print_header("5. ENDPOINTS DE DADOS DE MERCADO")
    
    # Teste 1: Candles
    success, resp = test_endpoint("POST", "/api/candles", json={
        "asset": "EURUSD",
        "timeframe": 5,
        "count": 10
    })
    print_test("POST /api/candles", success, f"Status {resp.get('status_code', 'N/A')}")
    if success and isinstance(resp.get("data"), list):
        print(f"  {Colors.BLUE}→ Candles recebidos: {len(resp['data'])}{Colors.END}")
    
    # Teste 2: Assets
    success, resp = test_endpoint("GET", "/api/assets")
    print_test("GET /api/assets", success, f"Status {resp.get('status_code', 'N/A')}")
    if success and "count" in resp.get("data", {}):
        print(f"  {Colors.BLUE}→ Total de ativos: {resp['data']['count']}{Colors.END}")

def test_documentation():
    """Testa documentação"""
    print_header("6. DOCUMENTACAO")
    
    # Teste 1: Swagger UI
    success, resp = test_endpoint("GET", "/docs")
    print_test("GET /docs (Swagger UI)", success, f"Status {resp.get('status_code', 'N/A')}")
    
    # Teste 2: ReDoc
    success, resp = test_endpoint("GET", "/redoc")
    print_test("GET /redoc (ReDoc)", success, f"Status {resp.get('status_code', 'N/A')}")

def print_summary():
    """Imprime resumo e próximos passos"""
    print_header("RESUMO E PROXIMOS PASSOS")
    
    print(f"{Colors.BLUE}URLs Importantes:{Colors.END}")
    print(f"  • API: {BASE_URL}/")
    print(f"  • Health: {BASE_URL}/health")
    print(f"  • Docs: {BASE_URL}/docs")
    print(f"  • ReDoc: {BASE_URL}/redoc")
    
    print(f"\n{Colors.BLUE}Se health retornar 404:{Colors.END}")
    print(f"  1. Verifique logs no Railway: https://railway.app")
    print(f"  2. Confirme SSID está correto em Variables")
    print(f"  3. Clique 'Redeploy' para reiniciar app")
    print(f"  4. Aguarde 2-3 minutos e teste novamente")
    
    print(f"\n{Colors.BLUE}Se health retornar erro de conexao (503):{Colors.END}")
    print(f"  1. SSID pode estar expirado")
    print(f"  2. Atualize SSID com novo valor do navegador")
    print(f"  3. Redeploy novamente")
    
    print(f"\n{Colors.BLUE}Endpoints Necessitam Conexao Ativa:{Colors.END}")
    print(f"  • POST /api/init (inicializar com SSID)")
    print(f"  • POST /api/connect (conectar)")
    print(f"  • GET /api/balance (requer conexao)")
    print(f"  • POST /api/order/place (requer conexao)")
    print(f"  • GET /api/candles (requer conexao)")

# ==================== MAIN ====================

def main():
    """Executa todos os testes"""
    print(f"\n{Colors.BOLD}{'=' * 70}{Colors.END}")
    print(f"{Colors.BOLD}{'TESTE COMPLETO - POCKETOPTION API RAILWAY'.center(70)}{Colors.END}")
    print(f"{Colors.BOLD}{'=' * 70}{Colors.END}")
    
    print(f"\n{Colors.YELLOW}Base URL: {BASE_URL}{Colors.END}")
    print(f"{Colors.YELLOW}Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}{Colors.END}")
    print(f"{Colors.YELLOW}SSID (primeiros 50 chars): {SSID[:50]}...{Colors.END}")
    
    # Executar testes
    test_server_health()
    time.sleep(0.5)
    
    test_documentation()
    time.sleep(0.5)
    
    test_account_endpoints()
    time.sleep(0.5)
    
    test_order_endpoints()
    time.sleep(0.5)
    
    test_market_endpoints()
    time.sleep(0.5)
    
    test_connection()
    
    # Resumo
    print_summary()
    
    print(f"\n{Colors.BOLD}{'=' * 70}{Colors.END}")
    print(f"{Colors.GREEN}✓ Testes completados!{Colors.END}")
    print(f"{Colors.BOLD}{'=' * 70}{Colors.END}\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Testes interrompidos pelo usuário{Colors.END}")
    except Exception as e:
        print(f"\n{Colors.RED}Erro: {e}{Colors.END}")
