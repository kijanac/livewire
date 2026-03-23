from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./data/bills.db"
    INGEST_INTERVAL_HOURS: int = 6
    LEGISTAR_BASE_URL: str = "https://webapi.legistar.com/v1"

    OPENROUTER_API_KEY: str = ""
    OPENROUTER_MODEL: str = "google/gemini-3-flash-preview"
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1/chat/completions"

    CITIES: dict = {
        "phoenix": {"name": "Phoenix", "state": "AZ"},
        "sanjose": {"name": "San Jose", "state": "CA"},
        "columbus": {"name": "Columbus", "state": "OH"},
        "seattle": {"name": "Seattle", "state": "WA"},
        "denver": {"name": "Denver", "state": "CO"},
        "nashville": {"name": "Nashville", "state": "TN"},
        "louisville": {"name": "Louisville", "state": "KY"},
        "boston": {"name": "Boston", "state": "MA"},
        "baltimore": {"name": "Baltimore", "state": "MD"},
        "milwaukee": {"name": "Milwaukee", "state": "WI"},
        "fresno": {"name": "Fresno", "state": "CA"},
        "sacramento": {"name": "Sacramento", "state": "CA"},
        "mesa": {"name": "Mesa", "state": "AZ"},
        "kansascity": {"name": "Kansas City", "state": "MO"},
        "coloradosprings": {"name": "Colorado Springs", "state": "CO"},
        "oakland": {"name": "Oakland", "state": "CA"},
        "lexington": {"name": "Lexington", "state": "KY"},
        "stockton": {"name": "Stockton", "state": "CA"},
        "corpuschristi": {"name": "Corpus Christi", "state": "TX"},
        "newark": {"name": "Newark", "state": "NJ"},
        "stpaul": {"name": "St. Paul", "state": "MN"},
        "pittsburgh": {"name": "Pittsburgh", "state": "PA"},
        "plano": {"name": "Plano", "state": "TX"},
        "madison": {"name": "Madison", "state": "WI"},
        "toledo": {"name": "Toledo", "state": "OH"},
    }

    model_config = {"env_file": ("../.env", ".env"), "extra": "ignore"}


settings = Settings()
