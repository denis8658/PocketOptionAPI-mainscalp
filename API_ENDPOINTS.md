# 🚀 PocketOption API - Endpoints para Uso Externo

Guia completo para expor e consumir a PocketOption API através de endpoints REST.

---

## 📋 Índice

1. [Configuração](#configuração)
2. [Iniciar Servidor](#iniciar-servidor)
3. [Endpoints Disponíveis](#endpoints-disponíveis)
4. [Exemplos de Uso](#exemplos-de-uso)
5. [Cliente Python](#cliente-python)
6. [Integração em Outros Projetos](#integração-em-outros-projetos)

---

## 🔧 Configuração

### 1. Instalar Dependências

```bash
# Dependências principais
pip install -r requirements.txt

# Dependências para API Server
pip install -r requirements-api.txt
```

### 2. Obter seu SSID

Para usar a API, você precisa de uma **SSID válida** no formato correto:

1. Abra [PocketOption](https://pocketoption.com) no navegador
2. Faça login
3. Abra **DevTools** (F12)
4. Vá para aba **Network**
5. Filtre por **WS** (WebSocket)
6. Procure mensagem começando com `42["auth"`
7. Copie a **mensagem completa** (incluindo `42["auth",...]`)

**Exemplo de SSID correto:**
```
42["auth",{"session":"n1p5ah5u8t9438rbunpgrq0hlq","isDemo":1,"uid":84402008,"platform":1}]
```

---

## ▶️ Iniciar Servidor

### Modo Desenvolvimento

```bash
python api_server.py
```

O servidor iniciará em `http://localhost:8000`

### Modo Produção

```bash
uvicorn api_server:app --host 0.0.0.0 --port 8000 --workers 4
```

### Verificar Status

```bash
curl http://localhost:8000/health
```

Resposta esperada:
```json
{
  "status": "healthy",
  "connected": false,
  "client_initialized": false,
  "timestamp": "2024-01-15T10:30:45.123456"
}
```

---

## 📡 Endpoints Disponíveis

### 🏥 Health & Info

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/` | Info do servidor |
| GET | `/health` | Status do servidor |
| GET | `/docs` | Swagger UI (documentação interativa) |
| GET | `/redoc` | ReDoc (documentação) |

### 🔐 Autenticação & Conexão

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/api/init` | Inicializa cliente com SSID |
| POST | `/api/connect` | Conecta ao PocketOption |
| POST | `/api/disconnect` | Desconecta |

### 💰 Conta

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/balance` | Obtém balanço da conta |
| GET | `/api/connection-stats` | Estatísticas de conexão |

### 📊 Ordens

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/api/order/place` | Coloca uma nova ordem |
| GET | `/api/orders/active` | Lista ordens ativas |

### 📈 Dados de Mercado

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/api/candles` | Obtém candles (histórico) |
| GET | `/api/assets` | Lista ativos disponíveis |

---

## 💻 Exemplos de Uso

### Ordens com expiracao em segundos

Use `duration_seconds` para enviar o tempo exato de expiracao:

```json
{
  "asset": "USDJPY_otc",
  "direction": "CALL",
  "amount": 1,
  "duration_seconds": 3
}
```

Para ordens, envie somente `duration_seconds`; `timeframe` fica reservado para candles. Ativos OTC podem aceitar expiracoes abaixo de 60 segundos. Para ativos nao-OTC, use `60`, `120`, `180`, `300`, `600`, `900` ou `1800`.

### Payouts

```bash
curl -X GET "http://localhost:8000/api/payouts"
curl -X GET "http://localhost:8000/api/payouts/EURUSD_otc"
```

### 1️⃣ Com curl

#### Inicializar Cliente

```bash
# Desenvolvimento
curl -X POST "http://localhost:8000/api/init" \
  -H "Content-Type: application/json" \
  -d '{
    "ssid": "42[\"auth\",{\"session\":\"YOUR_SESSION_HERE\",\"isDemo\":1,\"uid\":123456,\"platform\":1}]",
    "persistent_connection": false,
    "auto_reconnect": true,
    "connect_after_init": true
  }'

# Produção (Railway)
curl -X POST "https://pocketoptionapi-mainscalp.railway.internal/api/init" \
  -H "Content-Type: application/json" \
  -d '{
    "ssid": "42[\"auth\",{\"session\":\"YOUR_SESSION_HERE\",\"isDemo\":1,\"uid\":123456,\"platform\":1}]",
    "persistent_connection": false,
    "auto_reconnect": true,
    "connect_after_init": true
  }'
```

Para conta real ou demo, envie o SSID completo colado pelo usuario. A API extrai automaticamente `isDemo`, `uid` e `platform` do proprio SSID.

**Resposta:**
```json
{
  "status": "initialized",
  "demo": "true",
  "message": "Cliente inicializado. Agora use POST /api/connect"
}
```

#### Conectar

```bash
curl -X POST "http://localhost:8000/api/connect"
```

**Resposta:**
```json
{
  "status": "connected",
  "message": "Conectado com sucesso ao PocketOption"
}
```

#### Obter Balanço

```bash
curl -X GET "http://localhost:8000/api/balance"
```

**Resposta:**
```json
{
  "balance": 1250.50,
  "currency": "USD",
  "account_type": "demo",
  "timestamp": "2024-01-15T10:30:45.123456"
}
```

#### Colocar Ordem

```bash
curl -X POST "http://localhost:8000/api/order/place" \
  -H "Content-Type: application/json" \
  -d '{
    "asset": "EURUSD",
    "direction": "CALL",
    "amount": 10,
    "duration_seconds": 60
  }'
```

**Resposta:**
```json
{
  "request_id": "req_123456",
  "status": "accepted",
  "amount": 10,
  "asset": "EURUSD",
  "direction": "CALL",
  "duration_seconds": 60,
  "message": null
}
```

#### Obter Candles

```bash
curl -X POST "http://localhost:8000/api/candles" \
  -H "Content-Type: application/json" \
  -d '{
    "asset": "EURUSD",
    "timeframe": 5,
    "count": 10
  }'
```

**Resposta:**
```json
[
  {
    "open": 1.08765,
    "close": 1.08780,
    "high": 1.08795,
    "low": 1.08750,
    "timestamp": 1705318200
  },
  ...
]
```

#### Obter Ativos

```bash
curl -X GET "http://localhost:8000/api/assets"
```

**Resposta:**
```json
{
  "assets": {
    "EURUSD": "Euro vs US Dollar",
    "GBPUSD": "British Pound vs US Dollar",
    ...
  },
  "count": 50
}
```

---

### 2️⃣ Com Python

#### Usar o Cliente Incluído

```python
import asyncio
from examples.external_client_example import PocketOptionAPIClient

async def main():
    client = PocketOptionAPIClient(base_url="http://localhost:8000")
    
    try:
        # Verificar saúde
        health = await client.health_check()
        print(f"Servidor: {health['status']}")
        
        # Inicializar
        await client.init_client(
            ssid="42[\"auth\",{\"session\":\"YOUR_SESSION\",\"isDemo\":1,\"uid\":123456,\"platform\":1}]",
            is_demo=True
        )
        
        # Conectar
        await client.connect()
        
        # Obter balanço
        balance = await client.get_balance()
        print(f"Balanço: {balance['balance']} {balance['currency']}")
        
        # Obter candles
        candles = await client.get_candles("EURUSD", 5, count=50)
        print(f"Candles: {len(candles)}")
        
    finally:
        await client.disconnect()
        await client.close()

---

## 🔧 Configuração de URLs

### URLs Base

- **Desenvolvimento:** `http://localhost:8000`
- **Produção:** `https://pocketoptionapi-mainscalp.railway.internal`

### Configuração Automática (Python)

```python
from config import get_base_url, is_production

# Auto-detect baseado em variáveis de ambiente
base_url = get_base_url()  # Retorna produção se RAILWAY_ENVIRONMENT=1

# Ou especificar manualmente
base_url = get_base_url('prod')  # Força produção
base_url = get_base_url('dev')   # Força desenvolvimento

# Verificar ambiente
if is_production():
    print("Rodando em produção")
```

### Variáveis de Ambiente

Para forçar produção em desenvolvimento:
```bash
export PRODUCTION=1
# ou
export RAILWAY_ENVIRONMENT=production
```

### Cliente com Configuração Automática

```python
from examples.external_client_example import PocketOptionAPIClient

# Usa configuração automática
client = PocketOptionAPIClient()  # Auto-detect dev/prod

# Ou especificar manualmente
client = PocketOptionAPIClient("https://pocketoptionapi-mainscalp.railway.internal")
```

asyncio.run(main())
```

#### Usar httpx Diretamente

```python
import httpx
import asyncio

async def main():
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        # Inicializar
        response = await client.post("/api/init", json={
            "ssid": "42[\"auth\",{\"session\":\"YOUR_SESSION\",\"isDemo\":1,\"uid\":123456,\"platform\":1}]",
            "is_demo": True
        })
        print(response.json())
        
        # Conectar
        response = await client.post("/api/connect")
        print(response.json())
        
        # Obter balanço
        response = await client.get("/api/balance")
        print(response.json())

asyncio.run(main())
```

#### Usar requests (síncron)

```python
import requests
import time

# Inicializar
response = requests.post("http://localhost:8000/api/init", json={
    "ssid": "42[\"auth\",{\"session\":\"YOUR_SESSION\",\"isDemo\":1,\"uid\":123456,\"platform\":1}]",
    "is_demo": True
})
print(response.json())

# Conectar
response = requests.post("http://localhost:8000/api/connect")
print(response.json())

# Obter balanço
response = requests.get("http://localhost:8000/api/balance")
print(response.json())

# Colocar ordem
response = requests.post("http://localhost:8000/api/order/place", json={
    "asset": "EURUSD",
    "direction": "CALL",
    "amount": 10,
    "duration_seconds": 60
})
print(response.json())

# Desconectar
response = requests.post("http://localhost:8000/api/disconnect")
print(response.json())
```

---

### 3️⃣ Com JavaScript/Node.js

#### Fetch API

```javascript
const BASE_URL = "http://localhost:8000";

async function example() {
  try {
    // Inicializar
    let response = await fetch(`${BASE_URL}/api/init`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        ssid: '42["auth",{"session":"YOUR_SESSION","isDemo":1,"uid":123456,"platform":1}]',
        is_demo: true
      })
    });
    console.log(await response.json());
    
    // Conectar
    response = await fetch(`${BASE_URL}/api/connect`, { method: "POST" });
    console.log(await response.json());
    
    // Obter balanço
    response = await fetch(`${BASE_URL}/api/balance`);
    console.log(await response.json());
    
    // Obter candles
    response = await fetch(`${BASE_URL}/api/candles`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        asset: "EURUSD",
        timeframe: 5,
        count: 50
      })
    });
    console.log(await response.json());
    
  } catch (error) {
    console.error(error);
  }
}

example();
```

#### Axios

```javascript
const axios = require('axios');

const api = axios.create({
  baseURL: "http://localhost:8000"
});

async function example() {
  try {
    // Inicializar
    const init = await api.post('/api/init', {
      ssid: '42["auth",{"session":"YOUR_SESSION","isDemo":1,"uid":123456,"platform":1}]',
      is_demo: true
    });
    console.log(init.data);
    
    // Conectar
    const connect = await api.post('/api/connect');
    console.log(connect.data);
    
    // Obter balanço
    const balance = await api.get('/api/balance');
    console.log(balance.data);
    
  } catch (error) {
    console.error(error.response?.data || error.message);
  }
}

example();
```

---

## 🐍 Cliente Python

### Arquivo: `examples/external_client_example.py`

Já está incluído um cliente Python pronto para usar:

```python
from examples.external_client_example import PocketOptionAPIClient

# Criar cliente
client = PocketOptionAPIClient(base_url="http://localhost:8000")

# Usar todos os métodos disponíveis
await client.init_client(ssid="...")
await client.connect()
balance = await client.get_balance()
await client.place_order(asset="EURUSD", direction="CALL", amount=10, duration_seconds=60)
candles = await client.get_candles(asset="EURUSD", timeframe=5, count=50)
```

### Executar Exemplo

```bash
# 1. Terminal 1 - Iniciar servidor
python api_server.py

# 2. Terminal 2 - Executar cliente
python examples/external_client_example.py
```

---

## 🔗 Integração em Outros Projetos

### 1. FastAPI em outro projeto

```python
from fastapi import FastAPI
import httpx

app = FastAPI()
PO_API_URL = "http://localhost:8000"

@app.get("/trading/balance")
async def get_balance():
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{PO_API_URL}/api/balance")
        return response.json()
```

### 2. Flask em outro projeto

```python
from flask import Flask, jsonify
import requests

app = Flask(__name__)
PO_API_URL = "http://localhost:8000"

@app.route("/balance")
def get_balance():
    response = requests.get(f"{PO_API_URL}/api/balance")
    return jsonify(response.json())

if __name__ == "__main__":
    app.run()
```

### 3. Bot Discord

```python
import discord
from discord.ext import commands
import httpx

bot = commands.Bot(command_prefix="!")
PO_API_URL = "http://localhost:8000"

@bot.command(name="balance")
async def balance(ctx):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{PO_API_URL}/api/balance")
        data = response.json()
        await ctx.send(f"💰 Balanço: {data['balance']} {data['currency']}")

bot.run("YOUR_TOKEN")
```

### 4. Telegram Bot

```python
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import httpx

async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8000/api/balance")
        data = response.json()
        await update.message.reply_text(f"💰 Balanço: {data['balance']} {data['currency']}")

app = Application.builder().token("YOUR_TOKEN").build()
app.add_handler(CommandHandler("balance", balance_command))
app.run_polling()
```

### 5. Arquivo .env

Crie um `.env` para facilitar:

```bash
# .env
PO_API_URL=http://localhost:8000
PO_SSID=42["auth",{"session":"YOUR_SESSION","isDemo":1,"uid":123456,"platform":1}]
```

Use em qualquer projeto:

```python
from dotenv import load_dotenv
import os

load_dotenv()
PO_API_URL = os.getenv("PO_API_URL")
PO_SSID = os.getenv("PO_SSID")
```

---

## 🔒 Segurança

### Pontos Importantes

1. **Nunca compartilhe seu SSID** - é como sua senha
2. **Use HTTPS em produção** - não HTTP
3. **Adicione autenticação** ao servidor:

```python
from fastapi.security import HTTPBearer, HTTPAuthCredential
from fastapi import Depends

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthCredential = Depends(security)):
    if credentials.credentials != "your_secret_token":
        raise HTTPException(status_code=403)
    return credentials

@app.get("/api/balance", dependencies=[Depends(verify_token)])
async def get_balance(client: AsyncPocketOptionClient = Depends(get_client)):
    ...
```

4. **Rate limiting** - limite requisições por IP
5. **Validação de inputs** - já implementada com Pydantic

---

## ⚠️ Troubleshooting

### "Cliente não inicializado"
```
Solução: Use POST /api/init antes de /api/connect
```

### "Não conectado"
```
Solução: Use POST /api/connect depois de /api/init
```

### "SSID inválido"
```
Solução: Copie o formato completo: 42["auth",{...}]
Não apenas o session ID
```

### "Porta 8000 já em uso"
```bash
# Use outra porta
uvicorn api_server:app --port 8001
```

---

## 📚 Mais Informações

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **README Principal**: ../README.md

---

**Pronto para usar! 🚀**
