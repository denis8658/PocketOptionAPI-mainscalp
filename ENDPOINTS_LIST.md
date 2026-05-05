# 📡 PocketOption API - Lista Completa de Endpoints

## 🗂️ Índice Rápido

| Categoria | Endpoints |
|-----------|-----------|
| **Info** | 2 endpoints |
| **Connection** | 3 endpoints |
| **Account** | 2 endpoints |
| **Orders** | 2 endpoints |
| **Market Data** | 2 endpoints |
| **Total** | **11 endpoints** |

---

## 📋 Todos os Endpoints

---

## 📌 INFO

### ① GET `/`
**Descrição:** Informações do servidor  
**Autenticação:** Não requer  
**Resposta:** Informações básicas do servidor

```bash
curl -X GET "http://localhost:8000/"
```

**Response (200):**
```json
{
  "name": "PocketOption API Server",
  "version": "2.0.1",
  "status": "running",
  "docs": "/docs",
  "redoc": "/redoc"
}
```

---

### ② GET `/health`
**Descrição:** Verificar saúde do servidor e conexão  
**Autenticação:** Não requer  
**Resposta:** Status da conexão e inicialização

```bash
curl -X GET "http://localhost:8000/health"
```

**Response (200):**
```json
{
  "status": "healthy",
  "connected": false,
  "client_initialized": false,
  "timestamp": "2024-01-15T10:30:45.123456"
}
```

---

## 🔐 CONNECTION

### ③ POST `/api/init`
**Descrição:** Inicializar cliente com credenciais SSID  
**Autenticação:** Não requer  
**Body requerido:** ✅

```bash
curl -X POST "http://localhost:8000/api/init" \
  -H "Content-Type: application/json" \
  -d '{
    "ssid": "42[\"auth\",{\"session\":\"abc123...\",\"isDemo\":1,\"uid\":123456,\"platform\":1}]",
    "persistent_connection": false,
    "auto_reconnect": true,
    "connect_after_init": true
  }'
```

Para conta real ou demo, envie o SSID completo colado pelo usuario. A API extrai automaticamente `isDemo`, `uid` e `platform` do proprio SSID.

**Request Body:**
| Campo | Tipo | Obrigatório | Default | Descrição |
|-------|------|-------------|---------|-----------|
| `ssid` | string | ✅ | - | SSID completo do PocketOption |
| `is_demo` | boolean | ❌ | true | Usar conta demo |
| `region` | string | ❌ | null | Região preferida |
| `uid` | integer | ❌ | 0 | User ID |
| `platform` | integer | ❌ | 1 | Platform (1=web, 3=mobile) |
| `persistent_connection` | boolean | ❌ | false | Conexão persistente |
| `auto_reconnect` | boolean | ❌ | true | Auto-reconexão |
| `connect_after_init` | boolean | ❌ | false | Conectar automaticamente apos inicializar |

**Response (200):**
```json
{
  "status": "initialized",
  "demo": "true",
  "message": "Cliente inicializado. Agora use POST /api/connect"
}
```

**Errors:**
- **400**: SSID inválido ou formato incorreto

---

### ④ POST `/api/connect`
**Descrição:** Conectar ao servidor PocketOption  
**Autenticação:** Requer `/api/init` antes  
**Body requerido:** ❌

```bash
curl -X POST "http://localhost:8000/api/connect"
```

**Response (200):**
```json
{
  "status": "connected",
  "message": "Conectado com sucesso ao PocketOption"
}
```

**Errors:**
- **400**: Cliente não inicializado
- **500**: Falha ao conectar

---

### ⑤ POST `/api/disconnect`
**Descrição:** Desconectar do servidor PocketOption  
**Autenticação:** Não requer  
**Body requerido:** ❌

```bash
curl -X POST "http://localhost:8000/api/disconnect"
```

**Response (200):**
```json
{
  "status": "disconnected",
  "message": "Desconectado do PocketOption"
}
```

---

## 💰 ACCOUNT

### ⑥ GET `/api/balance`
**Descrição:** Obter saldo da conta  
**Autenticação:** Requer `/api/connect`  
**Body requerido:** ❌

```bash
curl -X GET "http://localhost:8000/api/balance"
```

**Response (200):**
```json
{
  "balance": 1250.50,
  "currency": "USD",
  "account_type": "demo",
  "timestamp": "2024-01-15T10:30:45.123456"
}
```

**Response Schema:**
| Campo | Tipo | Descrição |
|-------|------|-----------|
| `balance` | float | Saldo atual em moeda |
| `currency` | string | Código da moeda (USD, EUR, etc) |
| `account_type` | string | Tipo de conta (demo/live) |
| `timestamp` | string | Data/hora da requisição |

**Errors:**
- **400**: Cliente não inicializado
- **503**: Não conectado
- **500**: Erro ao obter balanço

---

### ⑦ GET `/api/connection-stats`
**Descrição:** Obter estatísticas de conexão  
**Autenticação:** Requer `/api/connect`  
**Body requerido:** ❌

```bash
curl -X GET "http://localhost:8000/api/connection-stats"
```

**Response (200):**
```json
{
  "total_connections": 5,
  "successful_connections": 5,
  "total_reconnects": 0,
  "last_ping_time": 1705318245.123,
  "messages_sent": 42,
  "messages_received": 38,
  "connection_start_time": 1705318200.0,
  "is_demo": true,
  "region": "DEMO",
  "uptime_seconds": 45.123
}
```

**Response Schema:**
| Campo | Tipo | Descrição |
|-------|------|-----------|
| `total_connections` | integer | Total de tentativas de conexão |
| `successful_connections` | integer | Conexões bem-sucedidas |
| `total_reconnects` | integer | Total de reconexões |
| `messages_sent` | integer | Mensagens enviadas |
| `messages_received` | integer | Mensagens recebidas |
| `uptime_seconds` | float | Tempo de atividade em segundos |

**Errors:**
- **400**: Cliente não inicializado
- **503**: Não conectado

---

## 📊 ORDERS

### ⑧ POST `/api/order/place`
**Descrição:** Colocar uma nova ordem de trading  
**Autenticação:** Requer `/api/connect`  
**Body requerido:** ✅

```bash
curl -X POST "http://localhost:8000/api/order/place" \
  -H "Content-Type: application/json" \
  -d '{
    "asset": "EURUSD",
    "direction": "CALL",
    "amount": 10.0,
    "timeframe": 5
  }'
```

**Request Body:**
| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `asset` | string | ✅ | Símbolo do ativo (ex: EURUSD) |
| `direction` | string | ✅ | CALL ou PUT |
| `amount` | float | ✅ | Valor da aposta em USD |
| `timeframe` | integer | ✅ | Tempo em minutos (1, 5, 15, 30, 60) |

**Response (200):**
```json
{
  "request_id": "req_abc123def456",
  "status": "accepted",
  "amount": 10.0,
  "asset": "EURUSD",
  "direction": "CALL",
  "timeframe": 5,
  "message": null
}
```

**Response Schema:**
| Campo | Tipo | Descrição |
|-------|------|-----------|
| `request_id` | string | ID único da requisição |
| `status` | string | Status da ordem (accepted/rejected/pending) |
| `amount` | float | Valor apostado |
| `asset` | string | Ativo negociado |
| `direction` | string | Direção da ordem |
| `timeframe` | integer | Timeframe da ordem |
| `message` | string | Mensagem adicional/erro |

**Valores Válidos:**
- **direction**: `CALL`, `PUT`
- **timeframe**: `1`, `5`, `15`, `30`, `60`
- **amount**: > 0 (mínimo depende da plataforma)

**Errors:**
- **400**: Cliente não inicializado ou parâmetros inválidos
- **503**: Não conectado
- **400**: Erro ao colocar ordem

---

### ⑨ GET `/api/orders/active`
**Descrição:** Obter lista de ordens ativas  
**Autenticação:** Requer `/api/connect`  
**Body requerido:** ❌

```bash
curl -X GET "http://localhost:8000/api/orders/active"
```

**Response (200):**
```json
[
  {
    "request_id": "req_abc123",
    "status": "open",
    "amount": 10.0,
    "asset": "EURUSD",
    "direction": "CALL",
    "timeframe": 5,
    "message": null
  },
  {
    "request_id": "req_def456",
    "status": "open",
    "amount": 5.0,
    "asset": "GBPUSD",
    "direction": "PUT",
    "timeframe": 15,
    "message": null
  }
]
```

**Response Schema:** Array de objetos com mesma estrutura do endpoint `/api/order/place`

**Errors:**
- **400**: Cliente não inicializado
- **503**: Não conectado
- **500**: Erro ao obter ordens

---

## 📈 MARKET DATA

### ⑩ POST `/api/candles`
**Descrição:** Obter candles (histórico de preços)  
**Autenticação:** Requer `/api/connect`  
**Body requerido:** ✅

```bash
curl -X POST "http://localhost:8000/api/candles" \
  -H "Content-Type: application/json" \
  -d '{
    "asset": "EURUSD",
    "timeframe": 5,
    "count": 50
  }'
```

**Request Body:**
| Campo | Tipo | Obrigatório | Default | Descrição |
|-------|------|-------------|---------|-----------|
| `asset` | string | ✅ | - | Símbolo do ativo |
| `timeframe` | integer | ✅ | - | Timeframe em minutos |
| `count` | integer | ❌ | 100 | Quantidade de candles |

**Response (200):**
```json
[
  {
    "open": 1.08765,
    "close": 1.08780,
    "high": 1.08795,
    "low": 1.08750,
    "timestamp": 1705318200
  },
  {
    "open": 1.08780,
    "close": 1.08795,
    "high": 1.08810,
    "low": 1.08770,
    "timestamp": 1705318260
  }
]
```

**Response Schema:** Array de velas com estrutura OHLC

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `open` | float | Preço de abertura |
| `close` | float | Preço de fechamento |
| `high` | float | Preço máximo |
| `low` | float | Preço mínimo |
| `timestamp` | integer | Unix timestamp |

**Timeframes Válidos:** `1`, `5`, `15`, `30`, `60`

**Errors:**
- **400**: Cliente não inicializado ou ativo inválido
- **503**: Não conectado

---

### ⑪ GET `/api/assets`
**Descrição:** Obter lista de ativos disponíveis  
**Autenticação:** Requer `/api/connect`  
**Body requerido:** ❌

```bash
curl -X GET "http://localhost:8000/api/assets"
```

**Response (200):**
```json
{
  "assets": {
    "EURUSD": "Euro vs US Dollar",
    "GBPUSD": "British Pound vs US Dollar",
    "USDJPY": "US Dollar vs Japanese Yen",
    "AUDUSD": "Australian Dollar vs US Dollar",
    "NZDUSD": "New Zealand Dollar vs US Dollar",
    "USDCAD": "US Dollar vs Canadian Dollar",
    "USDCHF": "US Dollar vs Swiss Franc",
    "EURGBP": "Euro vs British Pound"
  },
  "count": 50
}
```

**Response Schema:**
| Campo | Tipo | Descrição |
|-------|------|-----------|
| `assets` | object | Dicionário de ativos (símbolo → nome) |
| `count` | integer | Total de ativos disponíveis |

**Errors:**
- **400**: Cliente não inicializado
- **503**: Não conectado
- **500**: Erro ao obter ativos

---

## 🔄 Fluxo de Uso Recomendado

```
1. GET  /health                 ← Verificar servidor
2. POST /api/init               ← Inicializar com SSID
3. POST /api/connect            ← Conectar
4. GET  /api/balance            ← Ver saldo
5. GET  /api/assets             ← Ver ativos
6. POST /api/candles            ← Ver histórico
7. POST /api/order/place        ← Colocar ordem
8. GET  /api/orders/active      ← Ver ordens
9. GET  /api/connection-stats   ← Ver estatísticas
10. POST /api/disconnect        ← Desconectar
```

---

## 🔑 Códigos de Status HTTP

| Código | Significado |
|--------|------------|
| **200** | OK - Requisição bem-sucedida |
| **400** | Bad Request - Parâmetros inválidos ou cliente não inicializado |
| **401** | Unauthorized - Erro de autenticação |
| **403** | Forbidden - Acesso negado |
| **500** | Server Error - Erro interno do servidor |
| **503** | Service Unavailable - Não conectado ao PocketOption |

---

## 💡 Dicas

✅ **Sempre inicialize antes de conectar:**
```
/api/init → /api/connect
```

✅ **Verifique conexão antes de operações:**
```
GET /health
```

✅ **Use connection-stats para diagnosticar:**
```
GET /api/connection-stats
```

✅ **SSID tem prazo - renove se der erro:**
```
Obtenha novo SSID do navegador a cada 24h
```

---

## 📚 Documentação Interativa

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

---

**Versão:** 2.0.1  
**Última atualização:** 2024-01-15

---

## Market Data Cache

### GET `/api/ticks`
Obtem os ultimos ticks/precos em cache.

```bash
curl -X GET "http://localhost:8000/api/ticks"
```

### GET `/api/ticks/{asset}`
Obtem o ultimo tick/preco conhecido de um ativo.

```bash
curl -X GET "http://localhost:8000/api/ticks/EURUSD_otc"
```

### GET `/api/market/cache`
Obtem resumo do cache de candles e ticks alimentado pelo WebSocket.

```bash
curl -X GET "http://localhost:8000/api/market/cache"
```
