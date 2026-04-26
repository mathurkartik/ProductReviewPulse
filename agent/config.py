"""Configuration loading: pydantic-settings (env/.env) + products.yaml."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).parent.parent


# ---------------------------------------------------------------------------
# YAML-level models
# ---------------------------------------------------------------------------


class Recipients(BaseModel):
    to: list[str] = Field(default_factory=list)
    cc: list[str] = Field(default_factory=list)
    bcc: list[str] = Field(default_factory=list)


class ProductConfig(BaseModel):
    key: str
    display_name: str
    appstore_id: str | None = None
    play_package: str | None = None
    recipients: Recipients = Field(default_factory=Recipients)


class Defaults(BaseModel):
    window_weeks: int = 10
    embedding_model: str = "bge-small-en-v1.5"
    llm_provider: str = "groq"
    llm_model: str = "llama-3.3-70b-versatile"
    max_llm_cost_usd_per_run: float = 0.50
    hdbscan_min_cluster_size: int = 8
    confirm_send: bool = False


# ---------------------------------------------------------------------------
# Env / .env settings
# ---------------------------------------------------------------------------


class EnvSettings(BaseSettings):
    """Values sourced from environment variables or .env file."""

    model_config = SettingsConfigDict(
        env_file=ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    groq_api_key: str = ""
    mcp_server_url: str = ""
    confirm_send: bool = False
    pulse_env: str = "development"
    db_path: Path = ROOT / "data" / "pulse.db"


# ---------------------------------------------------------------------------
# Merged application config
# ---------------------------------------------------------------------------


class Settings(BaseModel):
    """Full application config: env vars + YAML product registry."""

    env: EnvSettings
    products: list[ProductConfig] = Field(default_factory=list)
    defaults: Defaults = Field(default_factory=Defaults)

    @property
    def effective_confirm_send(self) -> bool:
        """confirm_send is only honoured when PULSE_ENV=production.

        This prevents accidental email sends from development/staging.
        """
        if self.env.pulse_env != "production":
            return False
        return self.env.confirm_send

    def get_product(self, key: str) -> ProductConfig:
        for p in self.products:
            if p.key == key:
                return p
        valid = [p.key for p in self.products]
        raise KeyError(f"Unknown product key: {key!r}. Valid keys: {valid}")


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------


def _load_yaml(path: Path = ROOT / "products.yaml") -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def load_settings(yaml_path: Path | None = None) -> Settings:
    """Load and merge env + YAML config. Call once at process start."""
    env = EnvSettings()
    raw = _load_yaml(yaml_path or ROOT / "products.yaml")

    products: list[ProductConfig] = [ProductConfig(**p) for p in raw.get("products", [])]
    defaults = Defaults(**raw.get("defaults", {})) if "defaults" in raw else Defaults()

    return Settings(env=env, products=products, defaults=defaults)
