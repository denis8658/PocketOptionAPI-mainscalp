# 🚀 Guia de Hospedagem - PocketOption API Server

Completo guia para hospedar a API em diferentes plataformas

---

## 📋 Índice

1. [Opções de Hosting](#opções-de-hosting)
2. [Desenvolvimento Local](#desenvolvimento-local)
3. [VPS/Servidor Próprio](#vpsservidor-próprio)
4. [Docker](#docker)
5. [Plataformas em Nuvem](#plataformas-em-nuvem)
6. [Comparação de Serviços](#comparação-de-serviços)
7. [Segurança & Produção](#segurança--produção)

---

## 🎯 Opções de Hosting

| Opção | Custo | Dificuldade | Ideal Para |
|-------|-------|------------|-----------|
| **Localhost** | Grátis | ⭐ Muito Fácil | Desenvolvimento |
| **VPS Linux** | $3-20/mês | ⭐⭐ Médio | Produção |
| **Docker** | Varia | ⭐⭐ Médio | Qualquer lugar |
| **Heroku** | Grátis-$7/mês | ⭐ Fácil | Hobby/Produção |
| **Railway** | $5/mês | ⭐ Fácil | Hobby/Produção |
| **Render** | Grátis-$12/mês | ⭐ Fácil | Hobby/Produção |
| **AWS** | $0-100+/mês | ⭐⭐⭐ Complexo | Produção |
| **Google Cloud** | $0-100+/mês | ⭐⭐⭐ Complexo | Produção |
| **Azure** | $0-100+/mês | ⭐⭐⭐ Complexo | Produção |

---

## 💻 DESENVOLVIMENTO LOCAL

### Opção 1: Rodar Localmente

**Mais simples, sem custos**

```bash
# 1. Instalar dependências
pip install -r requirements.txt requirements-api.txt

# 2. Iniciar servidor
python api_server.py

# 3. Acessar
http://localhost:8000
http://localhost:8000/docs
```

**Pros:**
- ✅ Sem custos
- ✅ Sem latência
- ✅ Fácil debug

**Contras:**
- ❌ Só funciona no seu computador
- ❌ Precisa deixar rodando 24/7
- ❌ Acesso externo limitado

**Usar para:** Desenvolvimento e testes

---

## 🖥️ VPS/SERVIDOR PRÓPRIO

### Opção 2: VPS Linux (Recomendado para Produção)

**Melhor relação custo-benefício**

#### Provedores Recomendados

| Provedor | Preço | Specs | Link |
|----------|-------|-------|------|
| **Linode** | $5/mês | 1GB RAM, 1 vCPU | https://linode.com |
| **DigitalOcean** | $5/mês | 1GB RAM, 1 vCPU | https://digitalocean.com |
| **Vultr** | $2.50/mês | 512MB RAM, 1 vCPU | https://vultr.com |
| **Contabo** | €4/mês | 4GB RAM, 2 vCPU | https://contabo.com |
| **Hetzner** | €4/mês | 2GB RAM, 1 vCPU | https://hetzner.cloud |

#### Passo-a-Passo: DigitalOcean

##### 1. Criar Droplet

```
1. Acesse https://cloud.digitalocean.com
2. Clique "Create" → "Droplet"
3. Escolha imagem: "Ubuntu 22.04"
4. Escolha tamanho: "Basic" ($5/mês)
5. Escolha região: Próxima de você
6. Adicione SSH key (mais seguro)
7. Clique "Create Droplet"
```

##### 2. Conectar via SSH

```bash
# No seu PC
ssh root@YOUR_DROPLET_IP

# Ou se preferir password
# Você receberá por email
```

##### 3. Instalar Dependências

```bash
# Atualizar sistema
apt update && apt upgrade -y

# Instalar Python 3.11
apt install -y python3.11 python3.11-venv python3-pip

# Instalar Git
apt install -y git

# Instalar Nginx (para proxy reverso)
apt install -y nginx

# Instalar Supervisor (para gerenciar processo)
apt install -y supervisor
```

##### 4. Clonar Repositório

```bash
cd /home
git clone https://github.com/seu-usuario/PocketOptionAPI.git
cd PocketOptionAPI

# Criar virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt requirements-api.txt
```

##### 5. Configurar Arquivo .env

```bash
# Editar .env com suas credenciais
nano .env
```

```bash
SSID = 42["auth",{"session":"YOUR_SESSION","isDemo":1,"uid":123456,"platform":1}]
API_HOST = 0.0.0.0
API_PORT = 8000
LOG_LEVEL = INFO
```

**Salvar:** `CTRL+X` → `Y` → `ENTER`

##### 6. Configurar Supervisor (Rodar 24/7)

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
stderr_logfile=/var/log/pocketoption.err.log
stdout_logfile=/var/log/pocketoption.out.log
```

**Salvar e ativar:**
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start pocketoption
```

**Verificar status:**
```bash
sudo supervisorctl status pocketoption
```

##### 7. Configurar Nginx (Proxy Reverso)

```bash
sudo nano /etc/nginx/sites-available/pocketoption
```

```nginx
upstream pocketoption {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name seu-dominio.com;

    location / {
        proxy_pass http://pocketoption;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Documentação
    location /docs {
        proxy_pass http://pocketoption;
    }

    location /redoc {
        proxy_pass http://pocketoption;
    }
}
```

**Ativar:**
```bash
sudo ln -s /etc/nginx/sites-available/pocketoption /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

##### 8. Configurar SSL (HTTPS com Let's Encrypt)

```bash
# Instalar Certbot
sudo apt install -y certbot python3-certbot-nginx

# Gerar certificado
sudo certbot --nginx -d seu-dominio.com

# Renovação automática
sudo systemctl enable certbot.timer
```

##### 9. Testar

```bash
# Remoto
curl https://seu-dominio.com/health

# Docs
https://seu-dominio.com/docs
```

---

## 🐳 DOCKER

### Opção 3: Containerizar com Docker

**Melhor portabilidade e consistência**

#### 1. Construir Imagem Docker

```bash
# Já existe Dockerfile no projeto
docker build -t pocketoption-api:latest .
```

#### 2. Rodar Localmente

```bash
docker run -p 8000:8000 \
  -e SSID='42["auth",{...}]' \
  pocketoption-api:latest
```

#### 3. Com Docker Compose

```bash
# Já existe docker-compose.yml
docker-compose up -d
```

#### 4. Publicar Imagem (Docker Hub)

```bash
# Criar conta em https://hub.docker.com

# Login
docker login

# Tag da imagem
docker tag pocketoption-api:latest seu-usuario/pocketoption-api:latest

# Push
docker push seu-usuario/pocketoption-api:latest
```

#### 5. Deploy em VPS com Docker

```bash
# No servidor
ssh root@seu-vps

# Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Rodar container
docker run -d -p 80:8000 \
  -e SSID='42["auth",{...}]' \
  --restart always \
  seu-usuario/pocketoption-api:latest
```

---

## ☁️ PLATAFORMAS EM NUVEM

### Opção 4: Heroku (Fácil, Grátis/Pago)

#### 1. Instalar Heroku CLI

```bash
# Windows/macOS/Linux
https://devcenter.heroku.com/articles/heroku-cli
```

#### 2. Criar Arquivo `Procfile`

```bash
echo "web: uvicorn api_server:app --host 0.0.0.0 --port \$PORT" > Procfile
```

#### 3. Deploy

```bash
# Login
heroku login

# Criar app
heroku create seu-app-name

# Configurar variáveis
heroku config:set SSID='42["auth",{...}]'

# Deploy
git push heroku main

# Ver logs
heroku logs --tail
```

**URL:** https://seu-app-name.herokuapp.com

---

### Opção 5: Railway.app (Muito Fácil)

#### 1. Signup & Deploy

```bash
# Acesse https://railway.app
# Conecte sua conta GitHub
# Clique "New Project"
# Selecione seu repositório
```

#### 2. Configurar Variáveis

```
SSID = 42["auth",{...}]
```

#### 3. Deploy Automático

- Railway detecta `requirements.txt` automaticamente
- Faz deploy ao fazer push no GitHub
- Fornece URL pública

**Grátis até $5/mês, depois $5/mês**

---

### Opção 6: Render.com (Recomendado)

#### 1. Signup

```
https://render.com
```

#### 2. Conectar GitHub

```
1. Clique "New +"
2. Selecione "Web Service"
3. Conecte seu GitHub
4. Selecione repositório
```

#### 3. Configurar

```
Build: pip install -r requirements-api.txt
Start: uvicorn api_server:app --host 0.0.0.0 --port 10000
```

#### 4. Environment Variables

```
SSID=42["auth",{...}]
```

**Grátis: 750 horas/mês**  
**Pago: $12/mês (sempre ativo)**

---

### Opção 7: AWS (Produção Enterprise)

#### 1. Elastic Beanstalk (Mais Fácil)

```bash
# Instalar EB CLI
pip install awsebcli

# Inicializar
eb init -p python-3.11 pocketoption

# Criar ambiente
eb create pocketoption-env

# Deploy
eb deploy

# Abrir
eb open
```

#### 2. Configurar Variáveis

```bash
eb setenv SSID='42["auth",{...}]'
```

#### 3. Monitorar

```bash
eb status
eb logs
```

---

### Opção 8: Google Cloud Run

#### 1. Instalar Google Cloud SDK

```bash
# https://cloud.google.com/sdk
```

#### 2. Deploy

```bash
# Autenticar
gcloud auth login

# Deploy
gcloud run deploy pocketoption \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

#### 3. Variáveis de Ambiente

```bash
gcloud run services update pocketoption \
  --set-env-vars SSID='42["auth",{...}]'
```

---

### Opção 9: Azure (Microsoft)

#### 1. Criar App Service

```bash
# Instalar Azure CLI
# https://learn.microsoft.com/cli/azure

# Login
az login

# Criar grupo de recursos
az group create --name pocketoption --location eastus

# Criar app service
az appservice plan create --name pocketoption-plan --resource-group pocketoption --sku B1 --is-linux

# Criar app
az webapp create --resource-group pocketoption --plan pocketoption-plan --name pocketoption-api --runtime "python|3.11"

# Deploy via zip
az webapp deployment source config-zip --resource-group pocketoption --name pocketoption-api --src app.zip
```

---

## 📊 COMPARAÇÃO DE SERVIÇOS

| Serviço | Custo | Setup | Escalabilidade | Uptime | SSL | Melhor Para |
|---------|-------|-------|---|---|---|---|
| **Localhost** | $0 | 1min | ❌ | 24/7* | ❌ | Dev |
| **VPS (DO)** | $5/mês | 15min | ⭐⭐⭐ | 99.9% | ✅ | Produção |
| **Heroku** | Grátis/$7 | 5min | ⭐⭐ | 99.95% | ✅ | Hobby |
| **Railway** | Grátis/$5 | 3min | ⭐⭐ | 99.9% | ✅ | Hobby |
| **Render** | Grátis/$12 | 3min | ⭐⭐ | 99.95% | ✅ | Hobby/Prod |
| **AWS** | $0-100+ | 30min | ⭐⭐⭐⭐ | 99.99% | ✅ | Enterprise |
| **Google Cloud** | $0-100+ | 30min | ⭐⭐⭐⭐ | 99.99% | ✅ | Enterprise |
| **Azure** | $0-100+ | 30min | ⭐⭐⭐⭐ | 99.99% | ✅ | Enterprise |

---

## 🔒 SEGURANÇA & PRODUÇÃO

### Checklist de Segurança

#### 1. Credenciais

```bash
# ❌ NUNCA commite .env
# .gitignore deve ter:
.env
.env.local
secrets/
```

**Usar variáveis de ambiente:**
```bash
export SSID='42["auth",{...}]'
```

#### 2. Firewall

```bash
# Apenas portas necessárias
sudo ufw allow 22    # SSH
sudo ufw allow 80    # HTTP
sudo ufw allow 443   # HTTPS
sudo ufw enable
```

#### 3. Autenticação API

```python
# Adicionar token de autenticação
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def verify_token(credentials = Depends(security)):
    if credentials.credentials != os.getenv("API_TOKEN"):
        raise HTTPException(status_code=403)
    return credentials

@app.get("/api/balance", dependencies=[Depends(verify_token)])
async def get_balance(...):
    ...
```

#### 4. Rate Limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.get("/api/balance")
@limiter.limit("10/minute")
async def get_balance(...):
    ...
```

#### 5. HTTPS/SSL

```bash
# Let's Encrypt (Grátis)
sudo certbot certonly --standalone -d seu-dominio.com
```

#### 6. Logs e Monitoramento

```bash
# Verificar logs
tail -f /var/log/pocketoption.out.log

# Com Sentry para erros
pip install sentry-sdk
```

#### 7. Backup

```bash
# Fazer backup regularmente
tar -czf backup-$(date +%Y%m%d).tar.gz /home/PocketOptionAPI
```

---

## 🎯 RECOMENDAÇÃO FINAL

### Para Diferentes Cenários

**🏠 Hobby/Desenvolvimento:**
- ✅ Railway.app ou Render.com
- Grátis ou muito barato
- Deploy automático

**💼 Produção (Pequeno):**
- ✅ DigitalOcean VPS ($5/mês)
- Controle total
- Melhor preço

**🏢 Produção (Médio):**
- ✅ AWS ou Google Cloud
- Escalável
- Profissional

**🤖 Bot/Automação:**
- ✅ VPS dedicada
- Sempre ligado
- Confiável

---

## 📞 Suporte Rápido

| Problema | Solução |
|----------|---------|
| Porta 8000 já em uso | `lsof -i :8000` e `kill -9 PID` |
| Permissão negada SSH | `chmod 600 ~/.ssh/id_rsa` |
| Nginx não funciona | `sudo nginx -t` e `sudo systemctl restart nginx` |
| Python não encontrado | `which python3` |
| Module not found | `pip install -r requirements.txt` |

---

**Pronto para hospedar! 🚀**
