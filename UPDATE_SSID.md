# 🚀 Atualizar SSID no Railway

## Passo 1: Acesse Railway
```
https://railway.app
```

## Passo 2: Vá para seu projeto
```
PocketOptionAPI-mainscalp
```

## Passo 3: Atualize a variável SSID
```
1. Clique em "Variables" (ou Settings → Variables)
2. Encontre a variável "SSID"
3. Clique para editar
4. Cole o novo SSID:
   42["auth",{"session":"lg5c0491fc4j0q6ir66algo1al","isDemo":1,"uid":130669317,"platform":9,"isFastHistory":true,"isOptimized":true}]
5. Clique "Save"
```

## Passo 4: Redeploy
```
1. Vá para "Deployments"
2. Clique o botão de redeploy (ícone de refresh)
   OU
   Delete o deployment atual e deixe reconectar automaticamente
```

## Passo 5: Aguarde
```
Aguarde 2-3 minutos para o app reiniciar
```

## Passo 6: Teste
```bash
python test_railway_api.py
```

---

## ✅ Novo SSID Atualizado no Script

O arquivo `test_railway_api.py` já foi atualizado com o novo SSID.

Execute o teste após o redeploy:
```bash
python test_railway_api.py
```

---

## 📊 Status Esperado Após Redeploy

- ✅ GET /health → Status: healthy
- ✅ GET /docs → Status: 200
- ✅ POST /api/init → Status: 200 (inicializar)
- ✅ POST /api/connect → Status: 200 (conectar)
- ✅ GET /api/balance → Status: 200 (saldo)
- ✅ POST /api/candles → Status: 200 (dados de mercado)

---

**Pronto para testar! 🚀**