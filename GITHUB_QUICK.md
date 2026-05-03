# ⚡ GitHub Quick Commands

Copiar-colar os comandos abaixo. **Substitua seu-usuario e seu-email**

---

## 🚀 Primeira Vez - Setup Completo (5 min)

```powershell
# 1. Configurar Git
git config --global user.name "Seu Nome"
git config --global user.email "seu-email@gmail.com"

# 2. Navegar para projeto
cd C:\Users\denis\Desktop\PocketOptionAPI-mainscalp\PocketOptionAPI-mainscalp

# 3. Inicializar repositório
git init

# 4. Adicionar remote (copie URL do repositório criado em https://github.com/new)
git remote add origin https://github.com/seu-usuario/PocketOptionAPI-mainscalp.git

# 5. Adicionar todos os arquivos
git add .

# 6. Primeiro commit
git commit -m "Initial commit: FastAPI server with endpoints, Docker, and hosting guides"

# 7. Configurar branch main e fazer push
git branch -M main
git push -u origin main
```

**Pronto! Seu repositório está no GitHub** ✅

---

## 🔄 Próximas Vezes - Rotina Rápida

```powershell
# Apenas 3 comandos:
git add .
git commit -m "Sua mensagem aqui"
git push
```

---

## 💾 Exemplos de Mensagens de Commit

```bash
# Novo recurso
git commit -m "feat: Add authentication to API endpoints"

# Correção
git commit -m "fix: SSL configuration in Nginx"

# Documentação
git commit -m "docs: Update hosting guide with Railway example"

# Melhorias
git commit -m "improvement: Optimize Docker image size"

# Rápido/casual
git commit -m "Update: Minor improvements"
```

---

## 🎯 Checklist Antes de Fazer Push

```
☐ Arquivo .env NÃO foi adicionado (git status verifica)
☐ __pycache__ e .venv ignorados (.gitignore)
☐ Novo README com instruções
☐ Credenciais removidas do código
☐ Commits com mensagens claras
```

---

## 🐛 Erros Comuns

### "fatal: not a git repository"
```powershell
git init
```

### "remote origin already exists"
```powershell
git remote set-url origin https://seu-url-nova.git
```

### "Authentication failed"
```powershell
# Use token pessoal: https://github.com/settings/tokens
# Cole como password quando pedir
```

### "Permission denied (publickey)"
```powershell
# Use HTTPS ao invés de SSH
git remote set-url origin https://github.com/seu-usuario/repo.git
```

---

## 🎁 Script Automático (Windows)

Criamos um script `github-push.bat` para facilitar:

```powershell
# Copiar este arquivo para a raiz do projeto
# Depois executar:

.\github-push.bat "Sua mensagem de commit"

# Ou simplesmente:
.\github-push.bat
```

---

## 🔐 Como Gerar Token GitHub (Mais Seguro)

```
1. Acesse: https://github.com/settings/tokens
2. Clique "Generate new token"
3. Selecione "repo" (acesso completo)
4. Copie o token (use como senha no git push)
5. Salve em local seguro
```

---

## ✅ Verificar Status

```powershell
# Ver status
git status

# Ver commits
git log --oneline

# Ver remotes
git remote -v

# Ver branches
git branch -a
```

---

## 🚀 Começar Agora

1. Crie repositório: https://github.com/new
2. Copie URL HTTPS
3. Cole aqui → `git remote add origin SEU_URL_AQUI`
4. Execute os 3 comandos da rotina rápida acima
5. Feito! ✅

---

**Documentação completa: [GITHUB_GUIDE.md](GITHUB_GUIDE.md)**
