# Configuração da API - URLs Base

# ==================== URLs Base ====================

# Desenvolvimento (local)
BASE_URL_DEV = "http://localhost:8000"

# Produção (Railway)
BASE_URL_PROD = "https://pocketoptionapi-mainscalp.railway.internal"

# ==================== Como Usar ====================

# 1. Em código Python:
# from config import get_base_url
# base_url = get_base_url()

# 2. Em exemplos de curl:
# Substitua http://localhost:8000 pela URL apropriada

# 3. Em aplicações externas:
# Use a URL de produção quando hospedado no Railway

# ==================== Verificação ====================

# Para testar produção:
# curl https://pocketoptionapi-mainscalp.railway.internal/health

# Para testar desenvolvimento:
# curl http://localhost:8000/health
