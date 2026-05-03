# ⚡ Quick Deploy - 3 Formas Rápidas

Escolha uma forma e comece em minutos!

---

## 🟦 OPÇÃO 1: VPS Linux (DigitalOcean) - RECOMENDADO

**Custo:** $5/mês | **Tempo:** 15 minutos | **Ideal:** Produção

### Passo 1: Criar Conta e Droplet
```
1. https://digitalocean.com (ganha $200 em créditos)
2. Clique "Create" → "Droplet"
3. Ubuntu 22.04, $5/mês, escolha região próxima
4. Adicione SSH key (mais seguro)
5. Clique "Create"
```

### Passo 2: Conectar e Configurar
```bash
# Abra terminal
ssh root@SEU_IP_DO_DROPLET

# Atualizar
apt update && apt upgrade -y

# Instalar
apt install -y python3.11 python3.11-venv git nginx supervisor

# Clonar
cd /home
git clone https://github.com/seu-usuario/PocketOptionAPI.git
cd PocketOptionAPI

# Venv
python3.11 -m venv venv
source venv/bin/activate

# Instalar pacotes
pip install -r requirements.txt requirements-api.txt
```

### Passo 3: Arquivo .env
```bash
nano .env
```
```
SSID=42["auth",{"session":"SEU_SSID","isDemo":1,"uid":123456,"platform":1}]
API_HOST=0.0.0.0
API_PORT=8000
```

### Passo 4: Supervisor (Rodar 24/7)
```bash
sudo nano /etc/supervisor/conf.d/pocketoption.conf
```
```ini
[program:pocketoption]
directory=/home/PocketOptionAPI
command=/home/PocketOptionAPI/venv/bin/uvicorn api_server:app --host 0.0.0.0 --port 8000
user=root
autostart=true
autorestart=true
```

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start pocketoption
sudo supervisorctl status pocketoption
```

### Passo 5: Nginx (Proxy)
```bash
sudo nano /etc/nginx/sites-available/default
```
```nginx
upstream pocketoption {
    server 127.0.0.1:8000;
}

server {
    listen 80 default_server;
    server_name _;

    location / {
        proxy_pass http://pocketoption;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
sudo nginx -t
sudo systemctl restart nginx
```

### Passo 6: SSL Grátis
```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d seu-dominio.com
```

### Passo 7: Testar
```bash
curl http://seu-ip/health
# ou
https://seu-dominio.com/docs
```

**✅ Pronto!**

---

## 🟨 OPÇÃO 2: Railway.app - MÁS FÁCIL

**Custo:** Grátis-$5/mês | **Tempo:** 3 minutos | **Ideal:** Hobby

### Passo 1: Conectar GitHub
```
1. Acesse https://railway.app
2. Clique "Login" → "GitHub"
3. Autorize Railway
```

### Passo 2: Deploy
```
1. Clique "New Project"
2. Selecione seu repositório GitHub
3. Railway detecta Python automaticamente
4. Deploy em 1 minuto!
```

### Passo 3: Variáveis de Ambiente
```
1. Abra seu projeto em Railway
2. Vá para "Variables"
3. Adicione:
   SSID = 42["auth",{"session":"SEU_SSID","isDemo":1,"uid":123456,"platform":1}]
```

### Passo 4: Acessar
```
1. Vá para "Settings" → "Domain"
2. Clique "Generate Railway Domain"
3. Sua URL: https://seu-app-123.up.railway.app
```

**✅ Pronto!**

---

## 🟪 OPÇÃO 3: Docker + VPS

**Custo:** $5/mês | **Tempo:** 10 minutos | **Ideal:** Portabilidade

### Passo 1: Publicar Docker Hub
```bash
# Criar conta em https://hub.docker.com

# Fazer build
docker build -t seu-usuario/pocketoption:latest .

# Login
docker login

# Push
docker push seu-usuario/pocketoption:latest
```

### Passo 2: No VPS
```bash
# SSH
ssh root@seu-vps

# Instalar Docker
curl -fsSL https://get.docker.com | sh

# Rodar
docker run -d -p 80:8000 \
  -e SSID='42["auth",{...}]' \
  --restart always \
  seu-usuario/pocketoption:latest

# Testar
curl http://seu-ip/health
```

**✅ Pronto!**

---

## 📊 Comparação Rápida

| | VPS | Railway | Docker |
|---|---|---|---|
| **Custo** | $5/mês | Grátis-$5 | $5/mês |
| **Setup** | 15min | 3min | 10min |
| **Complexidade** | Média | Muito Fácil | Fácil |
| **Controle** | Total | Limitado | Total |
| **Uptime** | 99.9% | 99.9% | 99.9% |
| **SSL** | ✅ Grátis | ✅ Incluído | ✅ Nginx |
| **Escalabilidade** | ⭐⭐ | ⭐ | ⭐⭐⭐ |

---

## 🎯 Qual Escolher?

**Começando/Hobby:** 🟨 **Railway**
- Mais fácil
- Deploy automático
- Sem servidor para gerenciar

**Produção/Confiável:** 🟦 **VPS (DigitalOcean)**
- Melhor preço
- Controle total
- Profissional

**Portabilidade/Escalável:** 🟪 **Docker**
- Funciona em qualquer lugar
- Fácil de escalar
- Melhor para infraestrutura

---

## 🚨 Checklist Final

Antes de colocar em produção:

- [ ] SSID configurado no `.env` (nunca no código!)
- [ ] SSL/HTTPS habilitado
- [ ] Firewall configurado
- [ ] Logs e monitoramento
- [ ] Backup automático
- [ ] Autenticação na API
- [ ] Rate limiting
- [ ] Domínio configurado

---

## 📞 Troubleshooting

**Erro: "Connection refused"**
```bash
# Verificar se app está rodando
ps aux | grep uvicorn

# Reiniciar
sudo supervisorctl restart pocketoption
```

**Erro: "SSID inválido"**
```
1. Obtenha novo SSID do navegador
2. Atualize .env
3. Reinicie app
```

**Erro: "Port already in use"**
```bash
# Matar processo na porta 8000
lsof -i :8000
kill -9 <PID>
```

---

**Próximo passo: Escolha uma opção acima e comece!** 🚀
