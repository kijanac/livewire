from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./data/bills.db"
    INGEST_INTERVAL_HOURS: int = 6
    LEGISTAR_BASE_URL: str = "https://webapi.legistar.com/v1"

    OPENROUTER_API_KEY: str = ""
    OPENROUTER_MODEL: str = "google/gemini-3-flash-preview"
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1/chat/completions"

    CITIES: dict = {
        # Major metros
        "chicago": {"name": "Chicago", "state": "IL"},
        "sfgov": {"name": "San Francisco", "state": "CA"},
        "seattle": {"name": "Seattle", "state": "WA"},
        "denver": {"name": "Denver", "state": "CO"},
        "boston": {"name": "Boston", "state": "MA"},
        "phoenix": {"name": "Phoenix", "state": "AZ"},
        "sanantonio": {"name": "San Antonio", "state": "TX"},
        "detroit": {"name": "Detroit", "state": "MI"},
        "nashville": {"name": "Nashville", "state": "TN"},
        "louisville": {"name": "Louisville", "state": "KY"},
        "baltimore": {"name": "Baltimore", "state": "MD"},
        "milwaukee": {"name": "Milwaukee", "state": "WI"},
        "minneapolismn": {"name": "Minneapolis", "state": "MN"},
        "pittsburgh": {"name": "Pittsburgh", "state": "PA"},
        "richmondva": {"name": "Richmond", "state": "VA"},
        "providenceri": {"name": "Providence", "state": "RI"},
        # Mid-size cities
        "sanjose": {"name": "San Jose", "state": "CA"},
        "columbus": {"name": "Columbus", "state": "OH"},
        "oakland": {"name": "Oakland", "state": "CA"},
        "longbeach": {"name": "Long Beach", "state": "CA"},
        "sacramento": {"name": "Sacramento", "state": "CA"},
        "fresno": {"name": "Fresno", "state": "CA"},
        "stockton": {"name": "Stockton", "state": "CA"},
        "mesa": {"name": "Mesa", "state": "AZ"},
        "kansascity": {"name": "Kansas City", "state": "MO"},
        "coloradosprings": {"name": "Colorado Springs", "state": "CO"},
        "lexington": {"name": "Lexington", "state": "KY"},
        "corpuschristi": {"name": "Corpus Christi", "state": "TX"},
        "newark": {"name": "Newark", "state": "NJ"},
        "stpaul": {"name": "St. Paul", "state": "MN"},
        "plano": {"name": "Plano", "state": "TX"},
        "madison": {"name": "Madison", "state": "WI"},
        "toledo": {"name": "Toledo", "state": "OH"},
        "cabq": {"name": "Albuquerque", "state": "NM"},
        "alexandria": {"name": "Alexandria", "state": "VA"},
        "wilmington": {"name": "Wilmington", "state": "NC"},
        "gainesville": {"name": "Gainesville", "state": "FL"},
        "grandprairie": {"name": "Grand Prairie", "state": "TX"},
        "mckinney": {"name": "McKinney", "state": "TX"},
        "a2gov": {"name": "Ann Arbor", "state": "MI"},
        "jonesboro": {"name": "Jonesboro", "state": "AR"},
        # Counties
        "kingcounty": {"name": "King County", "state": "WA"},
    }

    model_config = {"env_file": ("../.env", ".env"), "extra": "ignore"}


settings = Settings()
