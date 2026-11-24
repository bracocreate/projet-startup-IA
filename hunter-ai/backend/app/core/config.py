"""Configuration de l'application, lue depuis les variables d'environnement / `.env`."""

from decimal import Decimal, InvalidOperation
from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

APP_VERSION = "0.1.0"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: Literal["development", "test", "production"] = "development"
    log_level: str = "INFO"
    app_timezone: str = "Europe/Paris"

    postgres_user: str = "hunter"
    postgres_password: SecretStr = SecretStr("")
    postgres_db: str = "hunter"
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    # Chaîne d'origines séparées par des virgules.
    cors_origins: str = Field(default="http://localhost:3000")

    # Jeton exigé pour les routes de modification (obligatoire en production).
    api_access_token: SecretStr = SecretStr("")

    # Seuil au-delà duquel les données sont signalées comme périmées (heures).
    stale_after_hours: int = 24

    # Taux de conversion vers l'EUR, ex. "USD=0.9512,GBP=1.1890". Vide par défaut : sans taux,
    # le prix EUR d'une offre en devise étrangère reste « non déterminé » (aucun taux inventé).
    fx_rates_to_eur: str = ""

    # --- eBay Browse API (connecteur officiel) ---
    ebay_client_id: str = ""
    ebay_client_secret: SecretStr = SecretStr("")
    ebay_environment: Literal["production", "sandbox"] = "production"
    ebay_marketplace_id: str = "EBAY_FR"
    # Plafond quotidien d'appels (eBay : 5 000/jour par défaut) ; marge de sécurité.
    ebay_daily_call_budget: int = Field(default=4500, ge=1, le=5000)

    @property
    def ebay_configured(self) -> bool:
        return bool(self.ebay_client_id and self.ebay_client_secret.get_secret_value())

    @field_validator("log_level")
    @classmethod
    def _upper(cls, v: str) -> str:
        return v.upper()

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def fx_rate_map(self) -> dict[str, Decimal]:
        rates: dict[str, Decimal] = {}
        for pair in self.fx_rates_to_eur.split(","):
            if not pair.strip():
                continue
            code, _, value = pair.partition("=")
            try:
                rate = Decimal(value.strip())
            except InvalidOperation as exc:
                raise ValueError(f"Taux de change invalide : {pair!r}") from exc
            if len(code.strip()) != 3 or not rate.is_finite() or rate <= 0:
                raise ValueError(f"Taux de change invalide : {pair!r}")
            rates[code.strip().upper()] = rate
        return rates

    @property
    def database_url(self) -> str:
        from sqlalchemy.engine import URL

        return URL.create(
            drivername="postgresql+psycopg",
            username=self.postgres_user,
            password=self.postgres_password.get_secret_value(),
            host=self.postgres_host,
            port=self.postgres_port,
            database=self.postgres_db,
        ).render_as_string(hide_password=False)


@lru_cache
def get_settings() -> Settings:
    return Settings()
