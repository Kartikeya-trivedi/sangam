"""Application settings, loaded from environment / .env.

Run uvicorn FROM backend/ so imports are package-relative (`from config import settings`).
The `.env` is searched in backend/ first, then the repo root (sangam/.env) so a single
root .env works for both `docker compose` and local `uvicorn`.

GRACEFUL DEGRADATION IS THE CONTRACT: every external key is optional. With no keys the app
still boots, seeds, and matches — Claude/Sarvam/InsightFace fall back to offline behaviour.
NEVER export ANTHROPIC_API_KEY in your Claude Code shell — it is app-side only.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_DIR = Path(__file__).resolve().parent
_ROOT_DIR = _BACKEND_DIR.parent
# Prefer backend/.env, fall back to repo-root .env.
_ENV_FILES = (_BACKEND_DIR / ".env", _ROOT_DIR / ".env")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=[str(p) for p in _ENV_FILES],
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- External APIs (all optional; app degrades when absent) ---
    # (env vars are matched case-insensitively by field name, e.g. ANTHROPIC_API_KEY)
    anthropic_api_key: str = ""
    sarvam_api_key: str = ""
    anthropic_model: str = "claude-opus-4-8"

    # --- Local database (SQLite for now; migrate to Postgres only if needed) ---
    # Stored next to the backend by default; override with SETU_DB_PATH.
    db_path: str = str(_BACKEND_DIR / "setu.db")

    # --- Face model (live-intake only) ---
    face_model: str = "buffalo_l"

    # --- Data retention (child-safety TTL auto-purge) ---
    ttl_days: int = 45

    # --- Matching thresholds ---
    high_confidence_threshold: float = 0.75  # proactive auto-notify
    review_threshold: float = 0.30           # minimum score surfaced to staff

    # --- Runtime ---
    offline_mode: bool = False

    @property
    def has_anthropic(self) -> bool:
        return bool(self.anthropic_api_key)

    @property
    def has_sarvam(self) -> bool:
        return bool(self.sarvam_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
