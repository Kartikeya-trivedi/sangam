"""Application settings, loaded from environment / .env (see .env.example, spec §17)."""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- External APIs (app-side only; NEVER export ANTHROPIC_API_KEY in the Claude Code shell, §14) ---
    anthropic_api_key: str = ""
    sarvam_api_key: str = ""
    anthropic_model: str = "claude-opus-4-8"

    # --- Central store (Supabase / pgvector) ---
    supabase_url: str = ""
    supabase_key: str = ""

    # --- Face model ---
    face_model: str = "buffalo_l"

    # --- Data retention (§12.4 TTL auto-purge) ---
    ttl_days: int = 45

    # --- Runtime ---
    # When True (or when cloud APIs are unreachable) the app serves from the local
    # FAISS mirror and degrades STT/Claude gracefully. See spec §13.
    offline_mode: bool = False

    @property
    def has_anthropic(self) -> bool:
        return bool(self.anthropic_api_key)

    @property
    def has_sarvam(self) -> bool:
        return bool(self.sarvam_api_key)

    @property
    def has_supabase(self) -> bool:
        return bool(self.supabase_url and self.supabase_key) and not self.offline_mode


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
