from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    # Ecoa o SQL gerado pela engine SQLAlchemy no log (útil para evidenciar N+1 no vídeo da
    # entrega). Fica desligado por padrão para não poluir os testes.
    SQLALCHEMY_ECHO: bool = False

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def SQLALCHEMY_DATABASE_URL(self) -> str:
        """DATABASE_URL (usada pelo pool psycopg em SQL cru) convertida para a URL de
        dialeto que o SQLAlchemy espera, mantendo o mesmo driver psycopg3 (sem asyncpg)."""
        url = self.DATABASE_URL
        if url.startswith("postgresql+psycopg://"):
            return url
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+psycopg://", 1)
        if url.startswith("postgres://"):
            return url.replace("postgres://", "postgresql+psycopg://", 1)
        return url


settings = Settings()
