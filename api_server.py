"""
FastAPI Server - PocketOption API Endpoints
Expõe a API PocketOption como endpoints REST para consumo externo
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
import asyncio
import json
import time
from datetime import datetime
import uvicorn
from loguru import logger

# Importar cliente PocketOption
from pocketoptionapi_async import (
    AsyncPocketOptionClient,
    OrderDirection,
    Balance,
    Order,
    OrderResult,
    AuthenticationError,
    ConnectionError,
)

# ==================== MODELS ====================

def parse_auth_payload(ssid: str) -> Dict[str, Any]:
    """Parse the JSON payload from a complete PocketOption auth SSID."""
    ssid = ssid.strip()

    if not ssid.startswith('42["auth",') and r'\"auth\"' in ssid:
        try:
            ssid = bytes(ssid, "utf-8").decode("unicode_escape")
        except Exception:
            pass

    json_start = ssid.find("{")
    json_end = ssid.rfind("}") + 1

    if not ssid.startswith('42["auth",') or json_start == -1 or json_end <= json_start:
        return {}

    json_part = ssid[json_start:json_end]

    try:
        return json.loads(json_part)
    except json.JSONDecodeError:
        # Some HTTP clients send the whole SSID escaped one extra time.
        try:
            unescaped = bytes(ssid, "utf-8").decode("unicode_escape")
            json_start = unescaped.find("{")
            json_end = unescaped.rfind("}") + 1
            if json_start != -1 and json_end > json_start:
                return json.loads(unescaped[json_start:json_end])
        except Exception:
            pass
        raise


def to_unix_timestamp(value: Any) -> int:
    """Convert datetime or numeric timestamps to Unix seconds for REST responses."""
    if isinstance(value, datetime):
        return int(value.timestamp())
    return int(float(value))

class ClientConfig(BaseModel):
    """Configuração para inicializar cliente"""
    ssid: str = Field(..., description="SSID no formato: 42[\"auth\",{\"session\":\"...\",\"isDemo\":1,\"uid\":...,\"platform\":1}]")
    is_demo: bool = Field(default=True, description="Usar conta demo")
    region: Optional[str] = Field(default=None, description="Região preferida")
    uid: int = Field(default=0, description="User ID")
    platform: int = Field(default=1, description="Platform (1=web, 3=mobile)")
    persistent_connection: bool = Field(default=False, description="Conexão persistente")
    auto_reconnect: bool = Field(default=True, description="Auto-reconexão")


    connect_after_init: bool = Field(default=False, description="Conectar automaticamente apos inicializar")

    @field_validator("ssid")
    @classmethod
    def normalize_ssid(cls, value: str) -> str:
        """Accept the pasted SSID and normalize common copy/paste issues."""
        if not isinstance(value, str):
            raise ValueError("SSID deve ser uma string")

        ssid = "".join(value.splitlines()).strip()

        if len(ssid) >= 2 and ssid[0] == ssid[-1] and ssid[0] in ("'", '"'):
            ssid = ssid[1:-1].strip()

        if not ssid.startswith('42["auth",') and r'\"auth\"' in ssid:
            try:
                unescaped = bytes(ssid, "utf-8").decode("unicode_escape").strip()
                if unescaped.startswith('42["auth",'):
                    ssid = unescaped
            except Exception:
                pass

        if not ssid:
            raise ValueError("SSID nao pode estar vazio")

        if ssid.startswith('42["auth",'):
            try:
                parse_auth_payload(ssid)
            except Exception as e:
                raise ValueError(f"SSID invalido: {e}") from e

        return ssid


class PlaceOrderRequest(BaseModel):
    """Request para colocar uma ordem"""
    asset: str = Field(..., description="Símbolo do ativo (ex: EURUSD)")
    direction: str = Field(..., description="Direção: CALL ou PUT")
    amount: float = Field(..., description="Valor da aposta")
    timeframe: int = Field(..., description="Tempo em minutos (1, 5, 15, 30, 60)")
    leverage: Optional[int] = Field(default=1, description="Alavancagem")


class GetCandlesRequest(BaseModel):
    """Request para obter candles"""
    asset: str = Field(..., description="Símbolo do ativo")
    timeframe: int = Field(..., description="Timeframe em minutos")
    count: int = Field(default=100, description="Quantidade de candles")


class BalanceResponse(BaseModel):
    """Response com saldo da conta"""
    balance: float
    currency: str
    account_type: str
    timestamp: str


class OrderResponse(BaseModel):
    """Response com resultado de ordem"""
    request_id: str
    status: str
    amount: float
    asset: str
    direction: str
    timeframe: int
    message: Optional[str] = None


class CandleData(BaseModel):
    """Dados de uma vela"""
    asset: Optional[str] = None
    timeframe: Optional[int] = None
    open: float
    close: float
    high: float
    low: float
    timestamp: int
    volume: Optional[float] = None


class HealthCheckResponse(BaseModel):
    """Response do health check"""
    status: str
    connected: bool
    client_initialized: bool
    timestamp: str


# ==================== GERENCIADOR DE CLIENTE ====================

class ClientManager:
    """Gerencia instância única do cliente"""
    
    def __init__(self):
        self.client: Optional[AsyncPocketOptionClient] = None
        self.is_connected = False
        self.config: Optional[ClientConfig] = None
    
    async def initialize(self, config: ClientConfig) -> bool:
        """Inicializa o cliente"""
        try:
            auth_payload = parse_auth_payload(config.ssid)
            is_demo = bool(auth_payload.get("isDemo", 1 if config.is_demo else 0))
            uid = int(auth_payload.get("uid", config.uid))
            platform = int(auth_payload.get("platform", config.platform))

            self.client = AsyncPocketOptionClient(
                ssid=config.ssid,
                is_demo=is_demo,
                region=config.region,
                uid=uid,
                platform=platform,
                persistent_connection=False,
                auto_reconnect=config.auto_reconnect,
                enable_logging=True
            )
            self.config = config.model_copy(update={
                "is_demo": is_demo,
                "uid": uid,
                "platform": platform,
                "persistent_connection": False,
            })
            logger.info(f"Cliente inicializado com sucesso (demo={is_demo}, uid={uid}, platform={platform})")
            return True
        except Exception as e:
            logger.error(f"Erro ao inicializar cliente: {e}")
            raise HTTPException(status_code=400, detail=f"Erro ao inicializar cliente: {str(e)}")
    
    async def connect(self) -> bool:
        """Conecta ao servidor PocketOption"""
        if not self.client:
            raise HTTPException(status_code=400, detail="Cliente não inicializado. Use /api/init primeiro")
        
        try:
            self.is_connected = await self.client.connect()
            if self.is_connected:
                logger.info("Conectado ao PocketOption")
            return self.is_connected
        except Exception as e:
            logger.error(f"Erro ao conectar: {e}")
            raise HTTPException(status_code=500, detail=f"Erro ao conectar: {str(e)}")
    
    async def disconnect(self):
        """Desconecta do servidor"""
        if self.client:
            try:
                await self.client.disconnect()
                self.is_connected = False
                logger.info("Desconectado do PocketOption")
            except Exception as e:
                logger.error(f"Erro ao desconectar: {e}")
    
    def get_client(self) -> AsyncPocketOptionClient:
        """Retorna o cliente ou lança exceção"""
        if not self.client:
            raise HTTPException(status_code=400, detail="Cliente não inicializado")
        if not self.is_connected:
            raise HTTPException(status_code=503, detail="Não conectado. Use /api/connect")
        return self.client


# ==================== INICIALIZAÇÃO DO FASTAPI ====================

app = FastAPI(
    title="PocketOption API Server",
    description="Servidor REST para API PocketOption com endpoints expostos",
    version="2.0.1",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gerenciador de cliente global
client_manager = ClientManager()


# ==================== DEPENDÊNCIAS ====================

async def get_client() -> AsyncPocketOptionClient:
    """Dependência para obter cliente conectado"""
    return client_manager.get_client()


# ==================== ENDPOINTS ====================

@app.get("/", tags=["Info"])
async def root():
    """Endpoint raiz com informações do servidor"""
    return {
        "name": "PocketOption API Server",
        "version": "2.0.1",
        "status": "running",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health", tags=["Health"], response_model=HealthCheckResponse)
async def health_check():
    """Verifica saúde do servidor e conexão"""
    return HealthCheckResponse(
        status="healthy",
        connected=client_manager.is_connected,
        client_initialized=client_manager.client is not None,
        timestamp=datetime.now().isoformat()
    )


# ==================== AUTENTICAÇÃO E CONEXÃO ====================

@app.post("/api/init", tags=["Connection"], response_model=Dict[str, str])
async def initialize_client(config: ClientConfig):
    """
    Inicializa o cliente com credenciais SSID
    
    **IMPORTANTE**: Use o formato completo de SSID:
    - ✅ Correto: `42["auth",{"session":"...","isDemo":1,"uid":...,"platform":1}]`
    - ❌ Errado: Apenas o session ID
    
    Para obter seu SSID:
    1. Acesse PocketOption no navegador
    2. Abra DevTools (F12)
    3. Vá para Network → Filter: WS
    4. Procure mensagem começando com `42["auth"`
    5. Copie a mensagem completa
    """
    await client_manager.initialize(config)

    if config.connect_after_init:
        connected = await client_manager.connect()
        if not connected:
            raise HTTPException(status_code=500, detail="Cliente inicializado, mas falhou ao conectar")
        return {
            "status": "connected",
            "demo": str(client_manager.config.is_demo if client_manager.config else config.is_demo),
            "message": "Cliente inicializado e conectado com sucesso"
        }

    return {
        "status": "initialized",
        "demo": str(client_manager.config.is_demo if client_manager.config else config.is_demo),
        "message": "Cliente inicializado. Agora use POST /api/connect"
    }


@app.post("/api/connect", tags=["Connection"], response_model=Dict[str, str])
async def connect():
    """Conecta ao servidor PocketOption"""
    connected = await client_manager.connect()
    if connected:
        return {
            "status": "connected",
            "message": "Conectado com sucesso ao PocketOption"
        }
    raise HTTPException(status_code=500, detail="Falha ao conectar")


@app.post("/api/disconnect", tags=["Connection"], response_model=Dict[str, str])
async def disconnect():
    """Desconecta do servidor PocketOption"""
    await client_manager.disconnect()
    return {
        "status": "disconnected",
        "message": "Desconectado do PocketOption"
    }


# ==================== CONTA ====================

@app.get("/api/balance", tags=["Account"], response_model=BalanceResponse)
async def get_balance(client: AsyncPocketOptionClient = Depends(get_client)):
    """Obtém saldo da conta"""
    try:
        balance = await client.get_balance()
        return BalanceResponse(
            balance=balance.balance,
            currency=balance.currency,
            account_type="demo" if client.is_demo else "live",
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        logger.error(f"Erro ao obter balanço: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao obter balanço: {str(e)}")


@app.get("/api/connection-stats", tags=["Account"], response_model=Dict[str, Any])
async def get_connection_stats(client: AsyncPocketOptionClient = Depends(get_client)):
    """Obtém estatísticas de conexão"""
    stats = client._connection_stats
    return {
        **stats,
        "is_demo": client.is_demo,
        "region": client.preferred_region,
        "uptime_seconds": time.time() - stats.get("connection_start_time", 0) if stats.get("connection_start_time") else 0
    }


# ==================== ORDENS ====================

@app.post("/api/order/place", tags=["Orders"], response_model=OrderResponse)
async def place_order(
    request: PlaceOrderRequest,
    client: AsyncPocketOptionClient = Depends(get_client)
):
    """
    Coloca uma ordem de trading
    
    Exemplo:
    ```json
    {
        "asset": "EURUSD",
        "direction": "CALL",
        "amount": 10,
        "timeframe": 5
    }
    ```
    """
    try:
        # Converter direção
        direction = OrderDirection.CALL if request.direction.upper() == "CALL" else OrderDirection.PUT
        
        # Colocar ordem
        order_result = await client.place_order(
            asset=request.asset,
            direction=direction,
            amount=request.amount,
            timeframe=request.timeframe,
        )
        
        return OrderResponse(
            request_id=order_result.request_id,
            status=order_result.status.value if hasattr(order_result.status, 'value') else str(order_result.status),
            amount=order_result.amount,
            asset=order_result.asset,
            direction=order_result.direction.value if hasattr(order_result.direction, 'value') else str(order_result.direction),
            timeframe=order_result.timeframe,
            message=order_result.message
        )
    except Exception as e:
        logger.error(f"Erro ao colocar ordem: {e}")
        raise HTTPException(status_code=400, detail=f"Erro ao colocar ordem: {str(e)}")


@app.get("/api/orders/active", tags=["Orders"], response_model=List[OrderResponse])
async def get_active_orders(client: AsyncPocketOptionClient = Depends(get_client)):
    """Obtém ordens ativas"""
    try:
        orders = await client.get_active_orders()
        return [
            OrderResponse(
                request_id=order.request_id,
                status=order.status.value if hasattr(order.status, 'value') else str(order.status),
                amount=order.amount,
                asset=order.asset,
                direction=order.direction.value if hasattr(order.direction, 'value') else str(order.direction),
                timeframe=order.timeframe,
                message=order.message
            )
            for order in orders
        ]
    except Exception as e:
        logger.error(f"Erro ao obter ordens ativas: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao obter ordens: {str(e)}")


# ==================== DADOS DE MERCADO ====================

@app.post("/api/candles", tags=["Market Data"], response_model=List[CandleData])
async def get_candles(
    request: GetCandlesRequest,
    client: AsyncPocketOptionClient = Depends(get_client)
):
    """
    Obtém candles (histórico de preços)
    
    Exemplo:
    ```json
    {
        "asset": "EURUSD",
        "timeframe": 5,
        "count": 50
    }
    ```
    """
    try:
        candles = await client.get_candles(
            asset=request.asset,
            timeframe=request.timeframe,
            count=request.count
        )
        candles = sorted(candles, key=lambda c: c.timestamp, reverse=True)[:request.count]
        
        return [
            CandleData(
                asset=getattr(c, "asset", request.asset),
                timeframe=getattr(c, "timeframe", request.timeframe),
                open=c.open,
                close=c.close,
                high=c.high,
                low=c.low,
                timestamp=to_unix_timestamp(c.timestamp),
                volume=getattr(c, "volume", None),
            )
            for c in candles
        ]
    except Exception as e:
        logger.error(f"Erro ao obter candles: {e}")
        raise HTTPException(status_code=400, detail=f"Erro ao obter candles: {str(e)}")


@app.get("/api/assets", tags=["Market Data"], response_model=Dict[str, Any])
async def get_assets(client: AsyncPocketOptionClient = Depends(get_client)):
    """Obtém lista de ativos disponíveis"""
    try:
        # Usar constantes do projeto
        from pocketoptionapi_async.constants import ASSETS
        return {
            "assets": ASSETS,
            "count": len(ASSETS)
        }
    except Exception as e:
        logger.error(f"Erro ao obter ativos: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao obter ativos: {str(e)}")


@app.get("/api/ticks", tags=["Market Data"], response_model=Dict[str, Any])
async def get_ticks(client: AsyncPocketOptionClient = Depends(get_client)):
    """Obtém o cache dos últimos ticks/preços recebidos."""
    return {
        "ticks": client.get_latest_ticks(),
        "count": len(client.get_latest_ticks()),
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/api/ticks/{asset}", tags=["Market Data"], response_model=Dict[str, Any])
async def get_tick(asset: str, client: AsyncPocketOptionClient = Depends(get_client)):
    """Obtém o último tick/preço conhecido de um ativo."""
    tick = client.get_latest_tick(asset)
    if not tick:
        raise HTTPException(
            status_code=404,
            detail=f"Nenhum tick em cache para {asset}. Chame /api/candles para esse ativo ou aguarde stream.",
        )
    return tick


@app.get("/api/market/cache", tags=["Market Data"], response_model=Dict[str, Any])
async def get_market_cache(client: AsyncPocketOptionClient = Depends(get_client)):
    """Obtém resumo do cache de dados de mercado alimentado pelo WebSocket."""
    return {
        "connected": client.is_connected,
        "ticks": client.get_latest_ticks(),
        "candles": {
            key: {
                "count": len(value),
                "last_timestamp": to_unix_timestamp(max(value, key=lambda c: c.timestamp).timestamp) if value else None,
                "last_close": max(value, key=lambda c: c.timestamp).close if value else None,
            }
            for key, value in client._candles_cache.items()
        },
        "last_stream_update": client._last_stream_update,
        "timestamp": datetime.now().isoformat(),
    }


# ==================== ERROR HANDLERS ====================

@app.exception_handler(AuthenticationError)
async def auth_error_handler(request, exc):
    return HTTPException(
        status_code=401,
        detail=f"Erro de autenticação: {str(exc)}"
    )


@app.exception_handler(ConnectionError)
async def connection_error_handler(request, exc):
    return HTTPException(
        status_code=503,
        detail=f"Erro de conexão: {str(exc)}"
    )


# ==================== STARTUP/SHUTDOWN ====================

@app.on_event("shutdown")
async def shutdown():
    """Desconecta ao desligar o servidor"""
    logger.info("Desligando servidor...")
    await client_manager.disconnect()


# ==================== MAIN ====================

if __name__ == "__main__":
    import time
    
    logger.info("Iniciando PocketOption API Server...")
    logger.info("Documentação disponível em: http://localhost:8000/docs")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
