# PocketSignalClient

Cliente separado da API para Windows. Ele usa a API hospedada em:

```text
https://pocketoptionapi-mainscalp-production-0434.up.railway.app
```

Na interface visual, essa raiz da API ja fica fixa dentro do sistema. O usuario nao precisa preencher nem alterar URL da API.

O programa nao abre WebSocket direto com a PocketOption. Ele chama os endpoints REST da API:

- `POST /api/init`
- `GET /health`
- `GET /api/balance`
- `GET /api/payouts/{asset}`
- `POST /api/candles`
- `POST /api/order/place`
- `GET /api/order/result/{request_id}`

## Rodar sem gerar EXE

```bat
cd signal_client
python pocket_signal_client.py
```

## Gerar EXE

Interface visual:

```bat
cd signal_client
build_gui_exe.bat
```

Saida:

```text
signal_client\dist\PocketSignalStudio.exe
```

Cliente de terminal:

```bat
cd signal_client
build_exe.bat
```

Saida:

```text
signal_client\dist\PocketSignalClient.exe
```

## Uso interativo

Interface visual:

```bat
PocketSignalStudio.exe
```

Ele abre uma interface local no navegador. Mantenha a janela do executavel aberta enquanto usa a tela.

Na interface:

- informe SSID e WebSocket URL opcional;
- a raiz da API ja esta embutida no sistema;
- deixe `Timeout da API em segundos` em `240` quando a conexao WebSocket estiver oscilando;
- clique em `Conectar`;
- escolha ativo, timeframe, quantidade de candles e confianca minima;
- clique em `Gerar Sinal`;
- envie a ordem somente se quiser executar o sinal.

Terminal:

```bat
PocketSignalClient.exe
```

O programa pede:

- SSID completo `42["auth",...]`
- `websocket_url` opcional

Depois mostra menu para saldo, payout, candles, diagnostico e ordem manual.

## Uso por comando

Saude da API:

```bat
PocketSignalClient.exe health
```

Inicializar sessao:

```bat
PocketSignalClient.exe --ssid "42[\"auth\",{\"session\":\"...\",\"isDemo\":1,\"uid\":9843526,\"platform\":9}]" init
```

Buscar candles:

```bat
PocketSignalClient.exe candles EURUSD_otc --timeframe 60 --count 100
```

Enviar ordem manual:

```bat
PocketSignalClient.exe order EURUSD_otc CALL 1 --duration-seconds 60 --wait
```

## Variaveis de ambiente opcionais

```bat
set PO_API_URL=https://pocketoptionapi-mainscalp-production-0434.up.railway.app
set PO_SSID=42["auth",{"session":"...","isDemo":1,"uid":9843526,"platform":9}]
set PO_WEBSOCKET_URL=wss://demo-api-eu.po.market/socket.io/?EIO=4^&transport=websocket
```

## Observacoes

Use `connect_after_init` apenas via comando `init`; o cliente nao chama `/api/connect` logo depois.
Para conta demo, prefira ativos OTC como `EURUSD_otc`.
