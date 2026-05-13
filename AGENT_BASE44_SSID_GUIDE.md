# Guia para o agente Base44 usar SSID

## Objetivo

O Base44 deve receber o SSID completo colado pelo usuario e enviar para a API sem tentar separar `session`, `uid`, `platform` ou `isDemo`.

A API ja extrai automaticamente:

- `isDemo`
- `uid`
- `platform`
- `session`

Nao existe SSID fixo no servidor. A cada chamada de `POST /api/init`, a API cria um novo cliente usando exatamente o `ssid` recebido no body. Se outro usuario enviar outro SSID depois, a sessao atual sera substituida por esse novo SSID.

Importante: esta API usa um cliente global por processo. Ela aceita varios formatos/tipos de SSID ao longo do tempo, mas nao mantem varias contas conectadas simultaneamente no mesmo processo.

## Endpoint de inicializacao

Use um unico POST:

```http
POST /api/init
Content-Type: application/json
```

Payload recomendado:

```json
{
  "ssid": "SSID_COMPLETO_COLADO_PELO_USUARIO",
  "websocket_url": "WEBSOCKET_URL_OPCIONAL_COPIADA_DO_NAVEGADOR",
  "connect_after_init": true
}
```

Nao envie apenas o `session_id`. O valor precisa comecar com:

```text
42["auth",{
```

## WebSocket URL opcional

Se o usuario conseguir copiar a URL WebSocket do navegador, envie tambem em `websocket_url`.
Esse campo e opcional. Quando informado, a API tenta essa URL primeiro e depois cai para as regioes padrao se ela falhar.

Exemplo de URL valida:

```text
wss://demo-api-eu.po.market/socket.io/?EIO=4&transport=websocket
```

Nao invente essa URL. Use apenas se ela vier do DevTools do navegador na conexao atual do usuario.

## Como montar o JSON no Base44

Se o usuario colar este SSID:

```text
42["auth",{"session":"...","isDemo":0,"uid":9843526,"platform":9,"isFastHistory":true,"isOptimized":true}]
```

O Base44 deve enviar como string JSON:

```json
{
  "ssid": "42[\"auth\",{\"session\":\"...\",\"isDemo\":0,\"uid\":9843526,\"platform\":9,\"isFastHistory\":true,\"isOptimized\":true}]",
  "websocket_url": "wss://api-eu.po.market/socket.io/?EIO=4&transport=websocket",
  "connect_after_init": true
}
```

Regra pratica para o agente:

- no formulario, mantenha o SSID como texto normal;
- na chamada HTTP, envie com `JSON.stringify`/cliente JSON normal;
- nao remova barras `\` dentro de SSID de conta real;
- nao tente converter manualmente `isDemo`;
- envie `websocket_url` somente se o usuario fornecer a URL WebSocket atual;
- nao envie `persistent_connection`.
- sempre chame `POST /api/init` quando o usuario trocar o SSID.
- se enviar `connect_after_init: true`, nao chame `POST /api/connect` logo depois.
  A propria chamada `/api/init` ja conecta e autentica.

## Conta real

SSID real geralmente tem `session` serializada com aspas escapadas:

```text
s:10:\"session_id\";
```

Isso esta correto. O agente nao deve limpar esses escapes.

## Validacao depois do init

Depois de `POST /api/init`, chamar:

```http
GET /health
GET /api/diagnostics
GET /api/balance
GET /api/payouts/EURUSD_otc
```

Esperado:

```json
{
  "connected": true,
  "client_initialized": true
}
```

Se `/api/init` falhar, chame:

```http
GET /api/diagnostics
```

Esse endpoint nao expoe o SSID e mostra:

```json
{
  "client_initialized": true,
  "connected": false,
  "demo": false,
  "uid": 9843526,
  "platform": 9,
  "account_type": "live",
  "last_connection_errors": []
}
```

Se `demo` aparecer `true` para um SSID real, o SSID foi enviado malformado ou nao contem `"isDemo":0`.

Se `failure_type` for `websocket_timeout`, nao conclua automaticamente que o SSID mudou ou expirou.
O SSID pode continuar igual e valido no navegador; nesse caso, tente novamente e prefira enviar a `websocket_url`
copiada da mesma conexao WebSocket onde o SSID foi visto.
A API tambem aceita `connection_attempts` opcional em `/api/init` para repetir automaticamente a conexao em caso de timeout.
Use entre `1` e `4`; recomendado `2` ou `3`.

Exemplo:

```json
{
  "ssid": "42[\"auth\",{\"session\":\"...\",\"isDemo\":1,\"uid\":9843526,\"platform\":9}]",
  "websocket_url": "wss://demo-api-eu.po.market/socket.io/?EIO=4&transport=websocket",
  "connect_after_init": true,
  "connection_attempts": 3
}
```

Se `failure_type` for `auth_or_session_failed`, copie novamente o SSID completo e a `websocket_url` da mesma sessao/aba.

## Ordens com tempo em segundos

Use `duration_seconds`:

```json
{
  "asset": "EURUSD_otc",
  "direction": "CALL",
  "amount": 1,
  "duration_seconds": 60
}
```

Valores aceitos dependem do ativo. Consulte:

```http
GET /api/payouts/EURUSD_otc
```

O campo `info.expirations` mostra os tempos validos em segundos, por exemplo:

```json
[60, 120, 180, 300, 600, 900]
```

## Resultado da ordem

Depois de enviar ordem, use o `request_id` retornado:

```http
GET /api/order/result/REQUEST_ID?timeout=180
```

Resposta:

```json
{
  "result": "win",
  "completed": true,
  "profit": 0.85,
  "balance_after": 2271.03
}
```
