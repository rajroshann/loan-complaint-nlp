from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # --- Database ---
    # SQLite for local dev (a single file, zero setup). Swapping to Postgres
    # later is just changing this one string in .env — no code change needed.
    DATABASE_URL: str = "sqlite:///./app.db"

    # --- JWT Auth ---
    JWT_SECRET_KEY: str          # no default on purpose — must be set in .env
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # --- LLM (for the SHAP -> explanation layer, added later) ---
    LLM_API_KEY: str = ""        # empty default so the app still runs before this is set
    LLM_PROVIDER: str = "anthropic"   # or "openai"

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    """
    lru_cache means this only actually reads/parses the .env file once,
    the first time it's called - every other call anywhere in the app
    returns the same cached object instantly, instead of re-reading the
    file on every request.
    """
    return Settings()


settings = get_settings()


if __name__ == "__main__":
    # Quick manual check - run this file directly to confirm your .env
    # is being read correctly, before anything else in the app depends on it.
    print("Database URL       :", settings.DATABASE_URL)
    print("JWT Algorithm       :", settings.JWT_ALGORITHM)
    print("Token expiry (mins) :", settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    print("LLM Provider        :", settings.LLM_PROVIDER)
    print("JWT Secret set?     :", bool(settings.JWT_SECRET_KEY))