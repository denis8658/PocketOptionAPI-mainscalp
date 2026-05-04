#!/usr/bin/env python3
"""
🚀 Inicialização da API PocketOption
Script para inicializar conexão e testar endpoints básicos
"""

import requests
import json
import time

# Configuração
BASE_URL = "https://pocketoptionapi-mainscalp-production-0434.up.railway.app"
SSID = '42["auth",{"session":"qrhc1u598e6m63htctj148upal","isDemo":1,"uid":9843526,"platform":9,"isFastHistory":true,"isOptimized":true}]'

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
    success, response = test_endpoint(
        "Inicialização",
        "POST",
        "/api/init",
        {"ssid": SSID},
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