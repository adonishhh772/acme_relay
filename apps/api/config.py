from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        populate_by_name=True,
    )

    database_url: str = "postgresql://relay:relay_secret@localhost:5434/relay_ops"
    redis_url: str = "redis://:redis_secret@localhost:6381/0"
    celery_broker_url: str = "redis://:redis_secret@localhost:6381/1"

    keycloak_url: str = "http://localhost:8080"
    keycloak_issuer: str = "http://localhost:8080"
    keycloak_realm: str = "acme"
    keycloak_client_id: str = "relay-backend"
    keycloak_frontend_client_id: str = "relay-frontend"
    keycloak_admin_user: str = Field(default="admin", alias="KEYCLOAK_ADMIN")
    keycloak_admin_password: str = Field(default="admin", alias="KEYCLOAK_ADMIN_PASSWORD")

    openai_api_key: str = ""
    openai_model: str = "gpt-4.1-mini"
    embedding_model: str = "text-embedding-3-small"
    embedding_dimension: int = 1536
    default_llm_provider: str = "openai"

    enable_mcp_agent_tools: bool = True
    mcp_domain_url: str = "http://localhost:8090"
    mcp_filesystem_url: str = "http://localhost:8091"
    mcp_postgres_url: str = "http://localhost:8092"
    mcp_connect_timeout_seconds: float = 10.0
    mcp_sse_read_timeout_seconds: float = 120.0

    enable_langfuse: bool = True
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "http://localhost:3001"
    langfuse_ui_url: str = "http://localhost:3001"
    langfuse_project_id: str = "relay-ops"

    enable_langsmith: bool = False
    langsmith_api_key: str = ""
    langsmith_project: str = "relay-agent"
    langsmith_org_id: str = ""
    langsmith_ui_url: str = "https://smith.langchain.com"

    enable_glitchtip: bool = True
    glitchtip_dsn: str = ""
    glitchtip_ui_url: str = "http://localhost:8001"

    grafana_ui_url: str = "http://localhost:3002"

    cors_origins: str = "http://localhost:5173"
    frontend_url: str = "http://localhost:5173"
    knowledge_root: str = "/data/knowledge"
    auth_disabled_for_tests: bool = False

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    @property
    def jwks_url(self) -> str:
        return (
            f"{self.keycloak_url}/realms/{self.keycloak_realm}"
            "/protocol/openid-connect/certs"
        )

    @property
    def issuer(self) -> str:
        return f"{self.keycloak_issuer}/realms/{self.keycloak_realm}"


@lru_cache
def get_settings() -> Settings:
    return Settings()
