"""
FastAPI Server - PocketOption API Endpoints
Expõe a API PocketOption como endpoints REST para consumo externo
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional, List, Dict, Any
import asyncio
import json
import os
import time
import sys
from urllib.parse import urlparse
from datetime import datetime
import uvicorn
from loguru import logger

logger.remove()
logger.add(sys.stdout, level="INFO")

# Importar cliente PocketOption
from pocketoptionapi_async import (
    AsyncPocketOptionClient,
    OrderDirection,
    Balance,
    Order,
    OrderResult,
    AuthenticationError,
    ConnectionError,
    REGIONS,
)

# ==================== MODELS ====================

DEMO_TIMEOUT_FALLBACK_REGIONS = [
    "SERVER1",
    "EUROPA",
    "UNITED_STATES",
    "FRANCE",
    "ASIA",
]

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


def is_demo_websocket_url(url: str) -> bool:
    """Return whether a PocketOption WebSocket URL is a demo gateway."""
    hostname = (urlparse(url).hostname or "").lower()
    return "demo" in hostname


def classify_connection_errors(
    errors: List[Dict[str, str]],
    is_demo: Optional[bool] = None,
    primary_url: Optional[str] = None,
) -> str:
    """Classifica falhas de conexao sem expor SSID."""
    messages = [error.get("error", "").lower() for error in errors]
    combined = " ".join(messages)

    if not combined:
        return "unknown"
    if has_authoritative_auth_rejection(errors, is_demo=is_demo, primary_url=primary_url):
        return "auth_or_session_failed"
    if "access" in combined or "acesso negado" in combined or "permission" in combined:
        return "network_access_denied"

    timeout_count = sum("timeout" in message or "timed out" in message for message in messages)

    if timeout_count:
        return "websocket_timeout"
    auth_count = sum("authentication" in message or "auth" in message or "ssid" in message for message in messages)
    if auth_count:
        return "auth_or_session_failed"
    if "failed to connect" in combined:
        return "websocket_unavailable"

    return "connection_failed"


def has_authoritative_auth_rejection(
    errors: List[Dict[str, str]],
    is_demo: Optional[bool] = None,
    primary_url: Optional[str] = None,
) -> bool:
    """Detect auth rejection from a gateway that should be trusted for this account."""
    for error in errors:
        message = error.get("error", "").lower()
        if "notauthorized" not in message and "invalid or expired ssid" not in message:
            continue

        url = error.get("url", "")
        if primary_url and url == primary_url:
            return True
        if is_demo is True and not is_demo_websocket_url(url):
            continue
        return True

    return False


def connection_next_steps(failure_type: str) -> List[str]:
    """Return actionable next steps for the current connection failure."""
    if failure_type == "auth_or_session_failed":
        return [
            "Obtenha um SSID novo no navegador. O servidor retornou NotAuthorized ou nao confirmou a autenticacao",
            "Copie a mensagem completa que comeca com 42[\"auth\",...] no DevTools -> Network -> WS",
            "Confirme se o body esta enviando o SSID completo, sem remover escapes da session",
            "Se informar websocket_url, use a URL WebSocket da mesma sessao em que copiou o SSID",
        ]
    if failure_type == "websocket_timeout":
        return [
            "Tente novamente, pois os gateways WebSocket da PocketOption podem oscilar mesmo com SSID valido",
            "Se possivel, envie websocket_url copiada da conexao atual do navegador",
            "Confirme se o servidor onde a API roda permite conexoes wss://*.po.market",
            "Se NotAuthorized ocorrer na propria websocket_url copiada do navegador, copie SSID e websocket_url novamente da mesma sessao",
        ]
    if failure_type == "network_access_denied":
        return [
            "Libere conexoes de saida wss://*.po.market no ambiente onde a API esta rodando",
            "Teste novamente depois de liberar firewall/proxy/sandbox",
        ]
    return [
        "Confirme se o SSID nao expirou",
        "Confirme se o body esta enviando o SSID completo com 42[\"auth\",...]",
        "Veja diagnostics.demo para confirmar se a API interpretou a conta como demo ou live",
        "Veja diagnostics.failure_type para separar bloqueio de rede, timeout ou sessao invalida",
    ]


def build_pair_payout_list(
    asset_full: Dict[str, Any],
    include_otc: bool = True,
    only_tradable: bool = True,
) -> List[Dict[str, Any]]:
    """Return forex/currency pairs with payout in a frontend-friendly list."""
    assets = asset_full.get("assets", {}) or {}
    payouts = asset_full.get("payouts", {}) or {}
    pairs: List[Dict[str, Any]] = []

    for symbol, info in assets.items():
        asset_type = str(info.get("type", "")).lower()
        is_currency_pair = asset_type in {"currency", "forex"}
        if not is_currency_pair:
            continue

        is_otc = bool(info.get("is_otc", symbol.endswith("_otc")))
        if is_otc and not include_otc:
            continue

        tradable = bool(info.get("tradable", False))
        if only_tradable and not tradable:
            continue

        payout = payouts.get(symbol, info.get("payout"))
        pairs.append(
            {
                "symbol": symbol,
                "name": info.get("name", symbol),
                "type": info.get("type"),
                "payout": payout,
                "payout_percent": float(payout) if payout is not None else None,
                "is_otc": is_otc,
                "tradable": tradable,
                "expirations": info.get("expirations", []),
            }
        )

    return sorted(
        pairs,
        key=lambda item: (
            item["payout_percent"] is not None,
            item["payout_percent"] or -1,
            item["symbol"],
        ),
        reverse=True,
    )

class ClientConfig(BaseModel):
    """Configuração para inicializar cliente"""
    ssid: str = Field(..., description="SSID no formato: 42[\"auth\",{\"session\":\"...\",\"isDemo\":1,\"uid\":...,\"platform\":1}]")
    is_demo: bool = Field(default=True, description="Usar conta demo")
    region: Optional[str] = Field(default=None, description="Região preferida")
    uid: int = Field(default=0, description="User ID")
    platform: int = Field(default=1, description="Platform (1=web, 3=mobile)")
    websocket_url: Optional[str] = Field(
        default=None,
        description="URL WebSocket opcional copiada do navegador para tentar antes das regioes padrao",
    )
    persistent_connection: bool = Field(default=False, description="Conexão persistente")
    auto_reconnect: bool = Field(default=True, description="Auto-reconexão")
    connection_attempts: int = Field(
        default=3,
        ge=1,
        le=4,
        description="Quantidade de tentativas quando houver timeout de WebSocket",
    )
    demo_timeout_fallback: bool = Field(
        default=True,
        description="Tentar gateways gerais quando conta demo falhar por timeout nos gateways demo",
    )

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

        if not ssid.startswith('42["auth",'):
            raise ValueError('SSID deve ser completo e comecar com 42["auth",')

        try:
            auth_payload = parse_auth_payload(ssid)
        except Exception as e:
            raise ValueError(f"SSID invalido: {e}") from e

        required_fields = ("session", "isDemo", "uid", "platform")
        missing_fields = [field for field in required_fields if field not in auth_payload]
        if missing_fields:
            raise ValueError(f"SSID incompleto. Campos ausentes: {', '.join(missing_fields)}")

        return ssid

    @field_validator("websocket_url")
    @classmethod
    def normalize_websocket_url(cls, value: Optional[str]) -> Optional[str]:
        """Accept an optional PocketOption WebSocket URL copied from DevTools."""
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError("websocket_url deve ser uma string")

        websocket_url = "".join(value.splitlines()).strip()
        if (
            len(websocket_url) >= 2
            and websocket_url[0] == websocket_url[-1]
            and websocket_url[0] in ("'", '"')
        ):
            websocket_url = websocket_url[1:-1].strip()
        if not websocket_url:
            return None

        parsed = urlparse(websocket_url)
        hostname = parsed.hostname or ""
        if parsed.scheme != "wss":
            raise ValueError("websocket_url deve comecar com wss://")
        if not (hostname == "po.market" or hostname.endswith(".po.market")):
            raise ValueError("websocket_url deve apontar para dominio po.market")
        if "/socket.io/" not in parsed.path:
            raise ValueError("websocket_url deve ser uma URL socket.io da PocketOption")

        return websocket_url


class PlaceOrderRequest(BaseModel):
    """Request para colocar uma ordem"""
    model_config = ConfigDict(extra="forbid")

    asset: str = Field(..., description="Símbolo do ativo (ex: EURUSD)")
    direction: str = Field(..., description="Direção: CALL ou PUT")
    amount: float = Field(..., description="Valor da aposta")
    duration_seconds: int = Field(..., ge=1, description="Tempo de expiracao em segundos")
    leverage: Optional[int] = Field(default=1, description="Alavancagem")

class GetCandlesRequest(BaseModel):
    """Request para obter candles"""
    asset: str = Field(..., description="Símbolo do ativo")
    timeframe: int = Field(..., description="Timeframe em minutos")
    count: int = Field(default=100, ge=1, le=1000, description="Quantidade de candles (maximo 1000)")


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
    duration_seconds: int
    payout: Optional[float] = None
    expires_at: Optional[str] = None
    message: Optional[str] = None


class OrderResultResponse(BaseModel):
    """Response com resultado final da ordem"""
    order_id: str
    result: str
    completed: bool
    status: str
    profit: float = 0
    balance_after: Optional[float] = None
    currency: Optional[str] = None
    timeout: bool = False


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
        self._connect_lock = asyncio.Lock()
    
    async def initialize(self, config: ClientConfig) -> bool:
        """Inicializa o cliente"""
        try:
            if self.client:
                await self.disconnect()
                self.client = None
                self.config = None

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

    def _config_from_environment(self) -> Optional[ClientConfig]:
        """Build client config from environment variables, if an SSID is configured."""
        ssid = os.getenv("POCKET_OPTION_SSID") or os.getenv("SSID")
        if not ssid:
            return None

        payload: Dict[str, Any] = {
            "ssid": ssid,
            "websocket_url": os.getenv("POCKET_OPTION_WEBSOCKET_URL") or os.getenv("WEBSOCKET_URL"),
            "region": os.getenv("POCKET_OPTION_REGION") or os.getenv("REGION"),
        }

        is_demo = os.getenv("POCKET_OPTION_IS_DEMO") or os.getenv("IS_DEMO")
        if is_demo is not None and is_demo.strip() != "":
            payload["is_demo"] = is_demo.strip().lower() in ("1", "true", "yes", "sim")

        attempts = os.getenv("POCKET_OPTION_CONNECTION_ATTEMPTS")
        if attempts:
            payload["connection_attempts"] = attempts

        return ClientConfig(**payload)

    def diagnostics(self) -> Dict[str, Any]:
        """Retorna diagnostico seguro da ultima inicializacao/conexao."""
        config = self.config
        client = self.client
        last_errors = getattr(client, "_last_connection_errors", []) if client else []
        failure_type = classify_connection_errors(
            last_errors,
            is_demo=config.is_demo if config else None,
            primary_url=config.websocket_url if config else None,
        )
        return {
            "client_initialized": client is not None,
            "connected": self.is_connected,
            "demo": config.is_demo if config else None,
            "uid": config.uid if config else None,
            "platform": config.platform if config else None,
            "account_type": "demo" if config and config.is_demo else "live" if config else None,
            "websocket_url_configured": bool(config and config.websocket_url),
            "connection_attempts_configured": config.connection_attempts if config else None,
            "demo_timeout_fallback": config.demo_timeout_fallback if config else None,
            "failure_type": failure_type,
            "last_connection_errors": last_errors,
        }

    def _connection_regions(self) -> Optional[List[str]]:
        """Build ordered connection targets, prioritizing explicit browser WebSocket URL."""
        if not self.client or not self.config:
            return None

        regions: List[str] = []
        seen_urls = set()

        def add_region(region: str) -> None:
            url = region if region.startswith("wss://") else REGIONS.get_region(region)
            dedupe_key = url or region
            if dedupe_key in seen_urls:
                return
            seen_urls.add(dedupe_key)
            regions.append(region)

        if self.config.websocket_url:
            add_region(self.config.websocket_url)
        if self.config.region and (not self.config.is_demo or "DEMO" in self.config.region.upper()):
            add_region(self.config.region)

        for region in self.client._get_default_regions():
            add_region(region)

        return regions or None

    def _demo_timeout_fallback_regions(self) -> Optional[List[str]]:
        """Fallback targets for demo sessions when demo gateways only time out."""
        if not self.client or not self.config or not self.config.is_demo:
            return None
        if not self.config.demo_timeout_fallback:
            return None

        regions: List[str] = []
        seen_urls = set()

        def add_region(region: str) -> None:
            url = region if region.startswith("wss://") else REGIONS.get_region(region)
            if not url or url in seen_urls:
                return
            seen_urls.add(url)
            regions.append(region)

        if self.config.websocket_url:
            add_region(self.config.websocket_url)
        for region in self.client._get_default_regions():
            add_region(region)
        for region in DEMO_TIMEOUT_FALLBACK_REGIONS:
            add_region(region)

        return regions or None
    
    async def connect(self) -> bool:
        """Conecta ao servidor PocketOption"""
        if not self.client:
            raise HTTPException(status_code=400, detail="Cliente não inicializado. Use /api/init primeiro")
        
        attempts = max(1, min(int(self.config.connection_attempts if self.config else 1), 4))
        regions = self._connection_regions()

        for attempt in range(1, attempts + 1):
            try:
                logger.info(f"Tentativa de conexao {attempt}/{attempts}")
                self.is_connected = await self.client.connect(regions=regions)
                if self.is_connected:
                    logger.info("Conectado ao PocketOption")
                    return True

                diagnostics = self.diagnostics()
                logger.warning(f"Falha ao conectar ao PocketOption: {diagnostics}")
                if diagnostics.get("failure_type") != "websocket_timeout":
                    return False

                if attempt >= attempts:
                    fallback_regions = self._demo_timeout_fallback_regions()
                    if fallback_regions and fallback_regions != regions:
                        logger.info("Tentando fallback de regioes para conta demo apos timeout")
                        try:
                            await self.client.disconnect()
                        except Exception as disconnect_error:
                            logger.debug(f"Erro limpando antes do fallback: {disconnect_error}")
                        self.is_connected = await self.client.connect(regions=fallback_regions)
                        if self.is_connected:
                            logger.info("Conectado ao PocketOption usando fallback de regioes")
                            return True
                    return False

                try:
                    await self.client.disconnect()
                except Exception as disconnect_error:
                    logger.debug(f"Erro limpando tentativa com timeout: {disconnect_error}")
                await asyncio.sleep(1.5 * attempt)
            except Exception as e:
                logger.error(f"Erro ao conectar: {e}")
                raise HTTPException(status_code=500, detail=f"Erro ao conectar: {str(e)}")

        return False

    async def ensure_connected(self) -> AsyncPocketOptionClient:
        """Return a connected client, initializing/reconnecting when possible."""
        async with self._connect_lock:
            if not self.client:
                env_config = self._config_from_environment()
                if not env_config:
                    raise HTTPException(
                        status_code=503,
                        detail={
                            "message": "Cliente nao inicializado. Use /api/init ou configure POCKET_OPTION_SSID/SSID no ambiente",
                            "next_steps": [
                                "Chame POST /api/init com connect_after_init=true antes de pedir candles",
                                "Ou configure POCKET_OPTION_SSID/SSID no ambiente para conexao automatica",
                            ],
                        },
                    )
                await self.initialize(env_config)

            if self.client and self.client.is_connected:
                self.is_connected = True
                return self.client

            self.is_connected = False
            connected = await self.connect()
            if connected and self.client:
                return self.client

            diagnostics = self.diagnostics()
            raise HTTPException(
                status_code=502,
                detail={
                    "message": "Nao foi possivel conectar ao PocketOption antes de executar a chamada",
                    "diagnostics": diagnostics,
                    "next_steps": connection_next_steps(diagnostics["failure_type"]),
                },
            )
    
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
    return await client_manager.ensure_connected()


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
            diagnostics = client_manager.diagnostics()
            raise HTTPException(
                status_code=502,
                detail={
                    "message": "Cliente inicializado, mas falhou ao conectar ao WebSocket da PocketOption",
                    "diagnostics": diagnostics,
                    "next_steps": connection_next_steps(diagnostics["failure_type"]),
                },
            )
        return {
            "status": "connected",
            "demo": str(client_manager.config.is_demo if client_manager.config else config.is_demo),
            "uid": str(client_manager.config.uid if client_manager.config else config.uid),
            "platform": str(client_manager.config.platform if client_manager.config else config.platform),
            "message": "Cliente inicializado e conectado com sucesso"
        }

    return {
        "status": "initialized",
        "demo": str(client_manager.config.is_demo if client_manager.config else config.is_demo),
        "uid": str(client_manager.config.uid if client_manager.config else config.uid),
        "platform": str(client_manager.config.platform if client_manager.config else config.platform),
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
    diagnostics = client_manager.diagnostics()
    raise HTTPException(
        status_code=502,
        detail={
            "message": "Falha ao conectar",
            "diagnostics": diagnostics,
            "next_steps": connection_next_steps(diagnostics["failure_type"]),
        },
    )


@app.get("/api/diagnostics", tags=["Connection"], response_model=Dict[str, Any])
async def diagnostics():
    """Retorna diagnostico da conexao atual sem expor o SSID."""
    return client_manager.diagnostics()


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
        "asset": "USDJPY_otc",
        "direction": "CALL",
        "amount": 10,
        "duration_seconds": 3
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
            duration=request.duration_seconds,
        )
        
        return OrderResponse(
            request_id=order_result.order_id,
            status=order_result.status.value if hasattr(order_result.status, 'value') else str(order_result.status),
            amount=order_result.amount,
            asset=order_result.asset,
            direction=order_result.direction.value if hasattr(order_result.direction, 'value') else str(order_result.direction),
            duration_seconds=order_result.duration,
            payout=order_result.payout,
            expires_at=order_result.expires_at.isoformat(),
            message=order_result.error_message
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
                request_id=order.order_id,
                status=order.status.value if hasattr(order.status, 'value') else str(order.status),
                amount=order.amount,
                asset=order.asset,
                direction=order.direction.value if hasattr(order.direction, 'value') else str(order.direction),
                duration_seconds=order.duration,
                payout=order.payout,
                expires_at=order.expires_at.isoformat(),
                message=order.error_message
            )
            for order in orders
        ]
    except Exception as e:
        logger.error(f"Erro ao obter ordens ativas: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao obter ordens: {str(e)}")


@app.get("/api/order/result/{order_id}", tags=["Orders"], response_model=OrderResultResponse)
async def get_order_result(
    order_id: str,
    timeout: float = 180.0,
    client: AsyncPocketOptionClient = Depends(get_client)
):
    """Aguarda e retorna o resultado final da ordem: win, loss, draw ou timeout."""
    try:
        result = await client.check_win(order_id, max_wait_time=timeout)
        if not result:
            raise HTTPException(status_code=404, detail="Resultado da ordem nao encontrado")

        balance = await client.get_balance(force_refresh=True) if result.get("completed", False) else None

        return OrderResultResponse(
            order_id=result.get("order_id", order_id),
            result=result.get("result", "unknown"),
            completed=bool(result.get("completed", False)),
            status=result.get("status", result.get("result", "unknown")),
            profit=float(result.get("profit", 0) or 0),
            balance_after=balance.balance if balance else None,
            currency=balance.currency if balance else None,
            timeout=bool(result.get("timeout", False)),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao verificar resultado da ordem: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao verificar resultado da ordem: {str(e)}")


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
        asset_full = client._get_asset_full()
        return {
            "assets": ASSETS,
            "asset_info": asset_full.get("assets", {}),
            "payouts": asset_full.get("payouts", {}),
            "count": len(ASSETS)
        }
    except Exception as e:
        logger.error(f"Erro ao obter ativos: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao obter ativos: {str(e)}")


@app.get("/api/payouts", tags=["Market Data"], response_model=Dict[str, Any])
async def get_payouts(client: AsyncPocketOptionClient = Depends(get_client)):
    """Obtém payout dos ativos recebidos pelo WebSocket."""
    asset_full = client._get_asset_full()
    payouts = asset_full.get("payouts", {})
    return {
        "payouts": payouts,
        "asset_info": asset_full.get("assets", {}),
        "count": len(payouts),
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/api/pairs/payouts", tags=["Market Data"], response_model=Dict[str, Any])
async def get_pairs_with_payouts(
    include_otc: bool = Query(default=True, description="Incluir pares OTC"),
    only_tradable: bool = Query(default=True, description="Listar apenas pares negociaveis"),
    client: AsyncPocketOptionClient = Depends(get_client),
):
    """Lista pares de moedas com payout em formato pronto para consumo."""
    asset_full = client._get_asset_full()
    pairs = build_pair_payout_list(
        asset_full,
        include_otc=include_otc,
        only_tradable=only_tradable,
    )
    return {
        "pairs": pairs,
        "count": len(pairs),
        "include_otc": include_otc,
        "only_tradable": only_tradable,
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/api/payouts/{asset}", tags=["Market Data"], response_model=Dict[str, Any])
async def get_payout(asset: str, client: AsyncPocketOptionClient = Depends(get_client)):
    """Obtém payout de um ativo específico."""
    payout = client.get_payout(asset)
    asset_info = client.get_asset_info(asset)

    if payout is None and not asset_info:
        raise HTTPException(
            status_code=404,
            detail=f"Payout nao encontrado para {asset}. Aguarde o WebSocket carregar payouts ou confira o nome do ativo.",
        )

    return {
        "asset": asset,
        "payout": payout,
        "info": asset_info,
        "timestamp": datetime.now().isoformat(),
    }


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
