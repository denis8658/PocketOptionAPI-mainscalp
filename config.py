"""
Configuração de URLs para diferentes ambientes
"""

import os
from typing import Optional


class APIConfig:
    """Configuração da API para diferentes ambientes"""

    # URLs base
    BASE_URL_DEV = "http://localhost:8000"
    BASE_URL_PROD = "https://pocketoptionapi-mainscalp.railway.internal"

    @classmethod
    def get_base_url(cls, environment: Optional[str] = None) -> str:
        """
        Retorna a URL base apropriada para o ambiente

        Args:
            environment: 'dev', 'prod', ou None (auto-detect)

        Returns:
            URL base da API
        """
        if environment == "prod":
            return cls.BASE_URL_PROD
        elif environment == "dev":
            return cls.BASE_URL_DEV

        # Auto-detect baseado em variáveis de ambiente
        if os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("PRODUCTION"):
            return cls.BASE_URL_PROD

        # Default para desenvolvimento
        return cls.BASE_URL_DEV

    @classmethod
    def is_production(cls) -> bool:
        """Verifica se está rodando em produção"""
        return cls.get_base_url() == cls.BASE_URL_PROD

    @classmethod
    def get_docs_url(cls) -> str:
        """Retorna URL da documentação Swagger"""
        return f"{cls.get_base_url()}/docs"

    @classmethod
    def get_redoc_url(cls) -> str:
        """Retorna URL da documentação ReDoc"""
        return f"{cls.get_base_url()}/redoc"

    @classmethod
    def get_health_url(cls) -> str:
        """Retorna URL do health check"""
        return f"{cls.get_base_url()}/health"


# Instância global
api_config = APIConfig()

# Funções de conveniência
def get_base_url(environment: Optional[str] = None) -> str:
    """Função de conveniência para obter URL base"""
    return APIConfig.get_base_url(environment)

def is_production() -> bool:
    """Função de conveniência para verificar produção"""
    return APIConfig.is_production()

# ==================== EXEMPLOS DE USO ====================

if __name__ == "__main__":
    print("=== Configuração da API ===")
    print(f"URL Base (auto): {get_base_url()}")
    print(f"URL Produção: {get_base_url('prod')}")
    print(f"URL Desenvolvimento: {get_base_url('dev')}")
    print(f"É produção: {is_production()}")
    print(f"Docs URL: {APIConfig.get_docs_url()}")
    print(f"Health URL: {APIConfig.get_health_url()}")

    print("\n=== Exemplos de uso ===")
    print("# Em código Python:")
    print("from config_urls import get_base_url")
    print("base_url = get_base_url()  # Auto-detect")
    print("base_url = get_base_url('prod')  # Força produção")

    print("\n# Em aplicações externas:")
    print("import os")
    print("os.environ['PRODUCTION'] = '1'  # Força produção")
    print("base_url = get_base_url()  # Retorna produção")