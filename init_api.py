#!/usr/bin/env python3
"""
🚀 Inicialização da API PocketOption
Script para inicializar conexão e testar endpoints básicos
"""

import requests
import json
import time

# Configuração
import os

BASE_URL = "https://pocketoptionapi-mainscalp-production-0434.up.railway.app"

# SSID diário (todo dia muda). Preferimos POCKET_OPTION_SSID, e fallback para SSID.
POCKET_OPTION_SSID = os.getenv("POCKET_OPTION_SSID") or os.getenv("SSID")

# is_demo opcional: pode ser setado manualmente (0/1 ou true/false).
# Se não for setado, o script não envia; o servidor pode usar is_demo padrão.
POCKET_OPTION_IS_DEMO = os.getenv("POCKET_OPTION_IS_DEMO") or os.getenv("IS_DEMO")

def test_endpoint(name, method, endpoint, data=None, expected_status=200):
    """Testa um endpoint específico"""
    url = f"{BASE_URL}{endpoint}"
    print(f"\n🔍 Testando {name}...")

    try:
        if method.upper() == "GET":
            response = requests.get(url, timeout=30)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, timeout=30)

        print(f"   Status: {response.status_code}")
        print(f"   URL: {url}")

        if response.status_code == expected_status:
            print("   ✅ Sucesso!")
            try:
                result = response.json()
                print(f"   📄 Resposta: {json.dumps(result, indent=2)[:200]}...")
            except:
                print(f"   📄 Resposta: {response.text[:200]}...")
        else:
            print("   ❌ Erro!")
            print(f"   📄 Resposta: {response.text}")

        return response.status_code == expected_status, response

    except Exception as e:
        print(f"   ❌ Erro de conexão: {e}")
        return False, None

def main():
    print("🚀 INICIALIZANDO API POCKETOPTION")
    print("=" * 50)

    # 1. Verificar servidor
    success, _ = test_endpoint("Servidor", "GET", "/")
    if not success:
        print("\n❌ Servidor não está respondendo!")
        return

    # 2. Verificar health
    success, _ = test_endpoint("Health Check", "GET", "/health")
    if not success:
        print("\n❌ Health check falhou!")
        return

    # 3. Inicializar conexão
    print("\n🔗 Inicializando conexão com PocketOption...")

    if not POCKET_OPTION_SSID:
        print("\n❌ Variável de ambiente SSID não definida.")
        print("Defina POCKET_OPTION_SSID (ou SSID) no ambiente/Railway com o SSID COMPLETO:")
        print('Exemplo: 42["auth",{"session":"...","isDemo":0,"uid":9843526,"platform":9}]')
        print('Exemplo demo: 42["auth",{"session":"...","isDemo":1,"uid":9843526,"platform":9}]')
        return

    init_payload: dict = {"ssid": POCKET_OPTION_SSID}

    # Envia is_demo apenas se o usuário setar a env var.
    # Se não enviar, o backend/cliente vai usar defaults.
    if POCKET_OPTION_IS_DEMO is not None and str(POCKET_OPTION_IS_DEMO).strip() != "":
        # Aceita valores: "0"/"1", "true"/"false"
        v = str(POCKET_OPTION_IS_DEMO).strip().lower()
        if v in ("1", "true", "yes"):
            init_payload["is_demo"] = True
        elif v in ("0", "false", "no"):
            init_payload["is_demo"] = False
        else:
            print(f"\n⚠️ POCKET_OPTION_IS_DEMO inválido: {POCKET_OPTION_IS_DEMO}. Use 0/1 ou true/false.")
            return

    success, response = test_endpoint(
        "Inicialização",
        "POST",
        "/api/init",
        init_payload,
        200
    )

    if success:
        print("\n✅ Conexão inicializada com sucesso!")

        # Aguardar um pouco
        print("⏳ Aguardando 3 segundos...")
        time.sleep(3)

        # 4. Conectar
        success, response = test_endpoint("Conexão", "POST", "/api/connect", {}, 200)

        if success:
            print("\n✅ Conectado ao PocketOption!")

            # Aguardar mais um pouco
            print("⏳ Aguardando 2 segundos...")
            time.sleep(2)

            # 5. Testar endpoints básicos
            print("\n🧪 Testando endpoints...")
            test_endpoint("Saldo", "GET", "/api/balance")
            test_endpoint("Ativos", "GET", "/api/assets")
            test_endpoint("Estatísticas", "GET", "/api/connection-stats")

        else:
            print("\n❌ Falha na conexão!")

    else:
        print("\n❌ Falha na inicialização!")
        print("Verifique se o SSID está correto e atualize no Railway se necessário.")

    print("\n" + "=" * 50)
    print("🏁 Teste concluído!")

if __name__ == "__main__":
    main()