# 📤 Guia: Enviar para GitHub

Passo-a-passo para colocar seu projeto no GitHub

---

## 📋 Pré-requisitos

- [ ] Conta GitHub criada (https://github.com/signup)
- [ ] Git instalado (`git --version`)
- [ ] Configurar Git globalmente

---

## ⚙️ Configurar Git (Primeira Vez)

```bash
git config --global user.name "Seu Nome"
git config --global user.email "seu-email@gmail.com"

# Verificar configuração
git config --global --list
```

---

## 🚀 Opção 1: Novo Repositório (Recomendado)

### Passo 1: Criar Repositório no GitHub

```
1. Acesse https://github.com/new
2. Nome: PocketOptionAPI-mainscalp
3. Descrição: "Comprehensive async Python API for PocketOption trading"
4. Escolha: Private (seguro) ou Public
5. NÃO marque "Add .gitignore" (já existe)
6. Clique "Create repository"
```

### Passo 2: Copiar URL

Na página do repositório criado, copie a URL HTTPS ou SSH:

```
HTTPS: https://github.com/seu-usuario/PocketOptionAPI-mainscalp.git
SSH:   git@github.com:seu-usuario/PocketOptionAPI-mainscalp.git
```

### Passo 3: No Terminal (PowerShell ou CMD)

```bash
# Navegar para o projeto
cd C:\Users\denis\Desktop\PocketOptionAPI-mainscalp\PocketOptionAPI-mainscalp

# Inicializar repositório local
git init

# Adicionar remote (substitua URL)
git remote add origin https://github.com/seu-usuario/PocketOptionAPI-mainscalp.git

# Verificar remote
git remote -v
```

### Passo 4: Adicionar Todos os Arquivos

```bash
# Adicionar tudo
git add .

# Verificar o que será commitado
git status
```

### Passo 5: Primeiro Commit

```bash
git commit -m "Initial commit: PocketOption API with FastAPI endpoints"
```

### Passo 6: Fazer Push

```bash
# Push para main/master (deixe o git criar automaticamente)
git branch -M main
git push -u origin main
```

### Passo 7: Verificar

```
Acesse: https://github.com/seu-usuario/PocketOptionAPI-mainscalp
```

---

## 🚀 Opção 2: Repositório Existente

Se já tem um `.git` local:

```bash
cd C:\Users\denis\Desktop\PocketOptionAPI-mainscalp\PocketOptionAPI-mainscalp

# Verificar remotes
git remote -v

# Se não houver, adicionar
git remote add origin https://github.com/seu-usuario/PocketOptionAPI-mainscalp.git

# Fazer push
git add .
git commit -m "Update: Add API server and hosting guides"
git push -u origin main
```

---

## 🔐 Opção 3: Com SSH (Mais Seguro)

### Gerar SSH Key

```bash
# Gerar chave (substitua seu email)
ssh-keygen -t ed25519 -C "seu-email@gmail.com"

# Ou se não tiver ed25519
ssh-keygen -t rsa -b 4096 -C "seu-email@gmail.com"

# Pressione ENTER para tudo
```

### Adicionar Chave ao GitHub

```bash
# Copiar chave pública (Windows)
type $env:USERPROFILE\.ssh\id_ed25519.pub | clip

# Ou Linux/Mac
cat ~/.ssh/id_ed25519.pub
```

```
1. Acesse https://github.com/settings/keys
2. Clique "New SSH key"
3. Cole a chave
4. Clique "Add SSH key"
```

### Usar SSH no Push

```bash
git remote set-url origin git@github.com:seu-usuario/PocketOptionAPI-mainscalp.git
git push -u origin main
```

---

## 📝 Arquivos Importantes para Incluir

Verifique se esses arquivos estão no repositório:

```
✅ api_server.py                 - Servidor FastAPI
✅ requirements.txt              - Dependências
✅ requirements-api.txt          - Dependências FastAPI
✅ docker-compose.yml            - Docker compose
✅ Dockerfile                    - Docker build
✅ .env.example                  - Template de variáveis
✅ .gitignore                    - Arquivos ignorados
✅ README.md                     - Documentação
✅ ENDPOINTS_LIST.md             - Lista de endpoints
✅ API_ENDPOINTS.md              - Guia de endpoints
✅ HOSTING_GUIDE.md              - Guia de hospedagem
✅ QUICK_DEPLOY.md               - Deploy rápido
✅ pocketoptionapi_async/        - Código principal
✅ examples/                     - Exemplos
✅ tests/                        - Testes
```

### ⚠️ IMPORTANTE: Não incluir

```
❌ .env                  - Credenciais reais
❌ wheels/              - Arquivos compilados
❌ __pycache__/         - Cache Python
❌ .venv/ ou venv/     - Virtual environment
```

---

## 📄 Criar/Atualizar .gitignore

Já existe, mas verifique que tem:

```bash
cat .gitignore
```

Se não existir ou incompleto:

```bash
# Criar .gitignore
echo "# Environment
.env
.env.local
.env.*.local

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
logs/
*.log

# Cache
.pytest_cache/
.coverage" > .gitignore

# Adicionar ao git
git add .gitignore
git commit -m "Add .gitignore"
git push
```

---

## 🔄 Commits Futuros (Rotina)

Depois que enviou a primeira vez:

```bash
# Fazer mudanças nos arquivos
# ...

# Verificar mudanças
git status

# Adicionar mudanças
git add .

# Commit
git commit -m "Descrição do que foi mudado"

# Push
git push
```

---

## 📊 Exemplo de Fluxo Completo

```bash
# 1. Navegar
cd C:\Users\denis\Desktop\PocketOptionAPI-mainscalp\PocketOptionAPI-mainscalp

# 2. Inicializar (só primeira vez)
git init

# 3. Adicionar remote (só primeira vez)
git remote add origin https://github.com/seu-usuario/PocketOptionAPI-mainscalp.git

# 4. Adicionar arquivos
git add .

# 5. Verificar
git status

# 6. Commit
git commit -m "Initial commit: FastAPI server with 11 endpoints and hosting guides"

# 7. Branch
git branch -M main

# 8. Push
git push -u origin main

# 9. Verificar online
# Abra https://github.com/seu-usuario/PocketOptionAPI-mainscalp
```

---

## 🎯 Informações do Repositório

Ao criar, recomendo preencher:

**Descrição:**
```
Comprehensive async Python API for PocketOption trading platform with FastAPI endpoints, Docker support, and multiple hosting options.
```

**Topics (Tópicos):**
```
python, fastapi, api, pocketoption, trading, async, websocket, docker, uvicorn, rest-api
```

**README.md** (adicionar ao final):

```markdown
## 🚀 Quick Start

### Development
```bash
pip install -r requirements.txt requirements-api.txt
python api_server.py
```

### Docker
```bash
docker-compose up -d
```

### Deployment
See [QUICK_DEPLOY.md](QUICK_DEPLOY.md) for Railway, VPS, and Docker options.

## 📡 API Endpoints

See [ENDPOINTS_LIST.md](ENDPOINTS_LIST.md) for complete documentation of all 11 endpoints.

## 📚 Documentation

- [API Endpoints](ENDPOINTS_LIST.md)
- [Hosting Guide](HOSTING_GUIDE.md)
- [Quick Deploy](QUICK_DEPLOY.md)
- [Original README](README.md)
```

---

## 🔗 Sincronizar Mudanças

Se você tem o repositório em múltiplos PCs:

```bash
# Atualizar local com remoto
git pull origin main

# Enviar mudanças locais
git push origin main
```

---

## 🐛 Troubleshooting

### Erro: "Repository not found"

```bash
# Verificar URL do remote
git remote -v

# Se errado, corrigir
git remote set-url origin https://github.com/seu-usuario/seu-repo.git
```

### Erro: "Permission denied"

```bash
# Usar HTTPS ao invés de SSH
git remote set-url origin https://github.com/seu-usuario/seu-repo.git

# Ou configurar SSH corretamente
# Ver seção "Opção 3: Com SSH"
```

### Erro: "Authentication failed"

```bash
# GitHub não aceita mais password
# Use token pessoal ou SSH

# Gerar token em: https://github.com/settings/tokens
# Usar como password ao fazer push
```

### Repositório Local Já Existe

```bash
# Se já existe .git mas remote está errado
git remote remove origin
git remote add origin https://github.com/seu-usuario/seu-repo.git
git branch -M main
git push -u origin main
```

---

## 📞 Próximos Passos

1. ✅ Criar repositório GitHub
2. ✅ Copiar URL
3. ✅ Fazer push (use comandos acima)
4. ✅ Adicionar README melhorado
5. ✅ Criar releases/tags para versões
6. ✅ Compartilhar link com amigos/colegas

---

## 🎁 Bônus: Adicionar Badges ao README

```markdown
# PocketOption API

![Python](https://img.shields.io/badge/Python-3.8+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Stars](https://img.shields.io/github/stars/seu-usuario/PocketOptionAPI-mainscalp?style=flat)
```

---

**Pronto para enviar? Use os comandos acima! 🚀**
