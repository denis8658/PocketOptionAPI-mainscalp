"""
Cliente Python para consumir endpoints do API Server PocketOption
Exemplo de como usar os endpoints em outro projeto
"""

import httpx
import asyncio
from typing import Optional, List, Dict, Any
import json
from config import get_base_url, is_production


class PocketOptionAPIClient:
    """Cliente para consumir endpoints REST do PocketOption"""
    
    def __init__(self, base_url: Optional[str] = None):
        """
        Inicializa o cliente
        
        Args:
            base_url: URL base da API. Se None, usa configuração automática
        """
        if base_url is None:
            base_url = get_base_url()
            print(f"🔗 Usando URL base: {base_url} ({'Produção' if is_production() else 'Desenvolvimento'})")
        
        self.base_url = base_url
        self.client = httpx.AsyncClient(base_url=base_url)
    
    async def close(self):
        """Fecha a conexão com o servidor"""
        await self.client.aclose()
    
    # ==================== CONNECTION ====================
    
    async def init_client(self, ssid: str, is_demo: bool = True, **kwargs) -> Dict[str, Any]:
        """Inicializa o cliente no servidor"""
        payload = {
            "ssid": ssid,
            "is_demo": is_demo,
            **kwargs
        }
        response = await self.client.post("/api/init", json=payload)
        response.raise_for_status()
        return response.json()
    
    async def connect(self) -> Dict[str, Any]:
        """Conecta ao PocketOption"""
        response = await self.client.post("/api/connect")
        response.raise_for_status()
        return response.json()
    
    async def disconnect(self) -> Dict[str, Any]:
        """Desconecta do PocketOption"""
        response = await self.client.post("/api/disconnect")
        response.raise_for_status()
        return response.json()
    
    async def health_check(self) -> Dict[str, Any]:
        """Verifica saúde do servidor"""
        response = await self.client.get("/health")
        response.raise_for_status()
        return response.json()
    
    # ==================== ACCOUNT ====================
    
    async def get_balance(self) -> Dict[str, Any]:
        """Obtém saldo da conta"""
        response = await self.client.get("/api/balance")
        response.raise_for_status()
        return response.json()
    
    async def get_connection_stats(self) -> Dict[str, Any]:
        """Obtém estatísticas de conexão"""
        response = await self.client.get("/api/connection-stats")
        response.raise_for_status()
        return response.json()
    
    # ==================== ORDERS ====================
    
    async def place_order(
        self,
        asset: str,
        direction: str,
        amount: float,
        timeframe: int
    ) -> Dict[str, Any]:
        """Coloca uma ordem"""
        payload = {
            "asset": asset,
            "direction": direction,
            "amount": amount,
            "timeframe": timeframe
        }
        response = await self.client.post("/api/order/place", json=payload)
        response.raise_for_status()
        return response.json()
    
    async def get_active_orders(self) -> List[Dict[str, Any]]:
        """Obtém ordens ativas"""
        response = await self.client.get("/api/orders/active")
        response.raise_for_status()
        return response.json()
    
    # ==================== MARKET DATA ====================
    
    async def get_candles(
        self,
        asset: str,
        timeframe: int,
        count: int = 100
    ) -> List[Dict[str, Any]]:
        """Obtém candles"""
        payload = {
            "asset": asset,
            "timeframe": timeframe,
            "count": count
        }
        response = await self.client.post("/api/candles", json=payload)
        response.raise_for_status()
        return response.json()
    
    async def get_assets(self) -> Dict[str, Any]:
        """Obtém lista de ativos"""
        response = await self.client.get("/api/assets")
        response.raise_for_status()
        return response.json()


# ==================== EXEMPLO DE USO ====================

async def main():
    """Exemplo de uso do cliente"""
    
    # Seu SSID - Obtenha do navegador como explicado no README
    SSID = '42["auth",{"session":"YOUR_SESSION_HERE","isDemo":1,"uid":123456,"platform":1}]'
    
    # Criar cliente (usa configuração automática)
    client = PocketOptionAPIClient()  # Auto-detect dev/prod
    
    # Ou especificar manualmente:
    # client = PocketOptionAPIClient(base_url="http://localhost:8000")  # Desenvolvimento
    # client = PocketOptionAPIClient(base_url="https://pocketoptionapi-mainscalp.railway.internal")  # Produção
    
    try:
        # 1. Verificar saúde do servidor
        print("🔍 Verificando saúde do servidor...")
        health = await client.health_check()
        print(f"   Status: {health['status']}")
        print(f"   Conectado: {health['connected']}")
        
        # 2. Inicializar cliente
        print("\n📝 Inicializando cliente...")
        init_result = await client.init_client(
            ssid=SSID,
            is_demo=True,
            persistent_connection=False,
            connect_after_init=True,
            auto_reconnect=True
        )
        print(f"   {init_result['message']}")
        
        # 3. Conectar
        print("\n🔌 Conectando ao PocketOption...")
        connect_result = await client.connect()
        print(f"   {connect_result['message']}")
        
        # 4. Obter balanço
        print("\n💰 Obtendo balanço...")
        balance = await client.get_balance()
        print(f"   Saldo: {balance['balance']} {balance['currency']}")
        print(f"   Tipo: {balance['account_type']}")
        
        # 5. Obter ativos disponíveis
        print("\n📊 Obtendo ativos disponíveis...")
        assets = await client.get_assets()
        print(f"   Total de ativos: {assets['count']}")
        print(f"   Primeiros 5: {list(assets['assets'].keys())[:5]}")
        
        # 6. Obter candles
        print("\n📈 Obtendo candles para EURUSD (5 min)...")
        candles = await client.get_candles(
            asset="EURUSD",
            timeframe=5,
            count=10
        )
        print(f"   Total de candles: {len(candles)}")
        if candles:
            latest = candles[-1]
            print(f"   Último: Open={latest['open']}, Close={latest['close']}")
        
        # 7. Colocar ordem (comentado para segurança)
        # print("\n🎯 Colocando ordem...")
        # order = await client.place_order(
        #     asset="EURUSD",
        #     direction="CALL",
        #     amount=1.0,
        #     timeframe=5
        # )
        # print(f"   Status: {order['status']}")
        # print(f"   Request ID: {order['request_id']}")
        
        # 8. Obter ordens ativas
        print("\n📋 Obtendo ordens ativas...")
        active_orders = await client.get_active_orders()
        print(f"   Total: {len(active_orders)}")
        
        # 9. Obter estatísticas
        print("\n📊 Estatísticas de conexão...")
        stats = await client.get_connection_stats()
        print(f"   Conexões bem-sucedidas: {stats['successful_connections']}")
        print(f"   Mensagens enviadas: {stats['messages_sent']}")
        
    except httpx.HTTPError as e:
        print(f"❌ Erro HTTP: {e}")
    except Exception as e:
        print(f"❌ Erro: {e}")
    finally:
        # 10. Desconectar
        print("\n🔌 Desconectando...")
        try:
            await client.disconnect()
            print("   ✅ Desconectado com sucesso")
        except:
            pass
        
        # Fechar cliente
        await client.close()


# ==================== USO EM REQUISIÇÕES HTTP DIRETAS ====================

EXAMPLES = {
    "curl_init": """
# 1. Inicializar cliente
curl -X POST "http://localhost:8000/api/init" \\
  -H "Content-Type: application/json" \\
  -d '{
    "ssid": "42[\\"auth\\",{\\"session\\":\\"YOUR_SESSION\\",\\"isDemo\\":1,\\"uid\\":123456,\\"platform\\":1}]",
    "is_demo": true,
    "persistent_connection": false,
    "connect_after_init": true
  }'
    """,
    
    "curl_connect": """
# 2. Conectar
curl -X POST "http://localhost:8000/api/connect"
    """,
    
    "curl_balance": """
# 3. Obter balanço
curl -X GET "http://localhost:8000/api/balance"
    """,
    
    "curl_place_order": """
# 4. Colocar ordem
curl -X POST "http://localhost:8000/api/order/place" \\
  -H "Content-Type: application/json" \\
  -d '{
    "asset": "EURUSD",
    "direction": "CALL",
    "amount": 10,
    "timeframe": 5
  }'
    """,
    
    "curl_candles": """
# 5. Obter candles
curl -X POST "http://localhost:8000/api/candles" \\
  -H "Content-Type: application/json" \\
  -d '{
    "asset": "EURUSD",
    "timeframe": 5,
    "count": 50
  }'
    """,
}


if __name__ == "__main__":
    # Descomente para executar o exemplo
    # asyncio.run(main())
    
    # Ou use os exemplos curl:
    print("=== EXEMPLOS CURL ===\n")
    for name, example in EXAMPLES.items():
        print(f"# {name.upper()}")
        print(example)
        print()
    
    print("\n=== Para executar o exemplo Python ===")
    print("1. Inicie o servidor: python api_server.py")
    print("2. Em outro terminal: python examples/external_client_example.py")
    print("3. Descomente a linha: asyncio.run(main())")
