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
  "connect_after_init": true
}
```

Nao envie apenas o `session_id`. O valor precisa comecar com:

```text
42["auth",{
```

## Como montar o JSON no Base44

Se o usuario colar este SSID:

```text
42["auth",{"session":"...","isDemo":0,"uid":9843526,"platform":9,"isFastHistory":true,"isOptimized":true}]
```

O Base44 deve enviar como string JSON:

```json
{
  "ssid": "42[\"auth\",{\"session\":\"...\",\"isDemo\":0,\"uid\":9843526,\"platform\":9,\"isFastHistory\":true,\"isOptimized\":true}]",
  "connect_after_init": true
}
```

Regra pratica para o agente:

- no formulario, mantenha o SSID como texto normal;
- na chamada HTTP, envie com `JSON.stringify`/cliente JSON normal;
- nao remova barras `\` dentro de SSID de conta real;
- nao tente converter manualmente `isDemo`;
- nao envie `persistent_connection`.
- sempre chame `POST /api/init` quando o usuario trocar o SSID.

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
