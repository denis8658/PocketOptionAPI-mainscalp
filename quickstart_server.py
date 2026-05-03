#!/usr/bin/env python3
"""
🚀 Quick Start - PocketOption API Server

Script para iniciar rápido o servidor API
Execute: python quickstart_server.py
"""

import subprocess
import sys
import time
import webbrowser
from pathlib import Path


def print_header(text):
    """Print seção com formatação"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60 + "\n")


def check_requirements():
    """Verifica se todas as dependências estão instaladas"""
    print_header("📋 Verificando Dependências")
    
    required_packages = {
        'fastapi': 'FastAPI',
        'uvicorn': 'Uvicorn',
        'httpx': 'HTTPX',
        'pocketoptionapi_async': 'PocketOption API Async'
    }
    
    missing = []
    for package, name in required_packages.items():
        try:
            __import__(package)
            print(f"  ✅ {name}")
        except ImportError:
            print(f"  ❌ {name} (faltando)")
            missing.append(package)
    
    if missing:
        print(f"\n⚠️  Instalando pacotes faltando...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements-api.txt"],
            check=True
        )
        print("✅ Dependências instaladas!")
    
    return len(missing) == 0


def get_ssid():
    """Solicita SSID do usuário"""
    print_header("🔐 Configuração do SSID")
    
    print("Para usar a API, você precisa do seu SSID da PocketOption.")
    print("\n📖 Como obter seu SSID:")
    print("  1. Abra PocketOption no navegador")
    print("  2. Abra DevTools (F12)")
    print("  3. Vá para Network → Filter: WS")
    print("  4. Procure mensagem começando com: 42[\"auth\",{...")
    print("  5. Copie a mensagem COMPLETA")
    print("\n✅ Exemplo correto:")
    print('   42["auth",{"session":"abc123...","isDemo":1,"uid":12345,"platform":1}]')
    print("\n❌ Exemplo ERRADO:")
    print("   abc123...  (apenas session ID)")
    
    while True:
        ssid = input("\n🔑 Cole seu SSID aqui: ").strip()
        
        if not ssid:
            print("⚠️  SSID não pode estar vazio!")
            continue
        
        if not ssid.startswith('42["auth"'):
            print("⚠️  SSID deve começar com: 42[\"auth\",{...")
            continue
        
        return ssid


def start_server(ssid):
    """Inicia o servidor"""
    print_header("🚀 Iniciando Servidor")
    
    # Salvar SSID em .env se necessário
    env_file = Path(".env")
    if not env_file.exists():
        print("📝 Criando arquivo .env...")
        with open(".env", "w") as f:
            f.write(f'SSID = "{ssid}"\n')
    
    print("🎯 O servidor será iniciado em: http://localhost:8000")
    print("\n📚 Endpoints disponíveis:")
    print("  • Documentação Swagger: http://localhost:8000/docs")
    print("  • Documentação ReDoc: http://localhost:8000/redoc")
    print("  • Health Check: http://localhost:8000/health")
    print("\n💡 Exemplos de uso:")
    print("  • Cliente Python: python examples/external_client_example.py")
    print("  • Curl: curl http://localhost:8000/api/balance")
    print("  • JavaScript: fetch('http://localhost:8000/api/balance')")
    
    print("\n⏳ Iniciando em 3 segundos...")
    time.sleep(3)
    
    print("\n✅ Servidor iniciado!")
    print("(Pressione CTRL+C para parar)\n")
    
    # Abrir navegador com documentação
    try:
        time.sleep(2)
        webbrowser.open("http://localhost:8000/docs")
    except:
        pass
    
    # Iniciar servidor
    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "api_server:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload"
        ])
    except KeyboardInterrupt:
        print("\n\n🛑 Servidor interrompido")


def main():
    """Fluxo principal"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + "  🚀 PocketOption API Server - Quick Start".ljust(59) + "║")
    print("║" + "  Expor endpoints para usar em outros projetos".ljust(59) + "║")
    print("╚" + "=" * 58 + "╝")
    
    # 1. Verificar dependências
    if not check_requirements():
        print("\n❌ Erro ao instalar dependências")
        sys.exit(1)
    
    # 2. Obter SSID
    ssid = get_ssid()
    
    # 3. Iniciar servidor
    start_server(ssid)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Até logo!")
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        sys.exit(1)
