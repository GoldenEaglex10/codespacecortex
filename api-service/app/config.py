from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    database_url_admin: str
    database_url_sync: str
    redis_url: str
    rate_limit_per_minute: int = 60
    auth_mode: str = "dev"
    jwt_dev_secret: str = ""
    jwt_audience: str = "cortex"
    jwt_issuer: str = "codespace"
    jwt_jwks_url: str = ""

    # App-level gateway key — required on every request, including /health.
    # This is separate from JWT auth: the API key gates "can you talk to this
    # API at all", the JWT gates "which tenant/student are you".
    api_key: str = ""

    # "dev" enables /docs, /redoc, /openapi.json. Any other value disables them.
    environment: str = "dev"

    # How long a cached /v1/chat response stays valid, in seconds.
    cache_ttl_seconds: int = 300

    class Config:
        env_file = ".env"

settings = Settings()
