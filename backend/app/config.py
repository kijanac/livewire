from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ENVIRONMENT: str = "dev"
    DATABASE_URL: str = "sqlite:///./data/bills.db"
    INGEST_INTERVAL_HOURS: int = 6
    LEGISTAR_BASE_URL: str = "https://webapi.legistar.com/v1"

    OPENROUTER_API_KEY: str = ""
    OPENROUTER_MODEL: str = "google/gemini-3-flash-preview"
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1/chat/completions"

    OPENSTATES_API_KEY: str = ""
    OPENSTATES_BASE_URL: str = "https://v3.openstates.org"
    OPENSTATES_PER_PAGE: int = 20
    OPENSTATES_LOOKBACK_DAYS: int = 2
    OPENSTATES_MAX_RETRIES_429: int = 4

    STORY_RETENTION_DAYS: int = 90

    SIMILAR_N: int = 10
    SIMILAR_BATCH: int = 50
    SIMILAR_THRESHOLD: float = 0.3

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

    STATES: dict = {
        "AL": {"name": "Alabama"},
        "AK": {"name": "Alaska"},
        "AZ": {"name": "Arizona"},
        "AR": {"name": "Arkansas"},
        "CA": {"name": "California"},
        "CO": {"name": "Colorado"},
        "CT": {"name": "Connecticut"},
        "DE": {"name": "Delaware"},
        "FL": {"name": "Florida"},
        "GA": {"name": "Georgia"},
        "HI": {"name": "Hawaii"},
        "ID": {"name": "Idaho"},
        "IL": {"name": "Illinois"},
        "IN": {"name": "Indiana"},
        "IA": {"name": "Iowa"},
        "KS": {"name": "Kansas"},
        "KY": {"name": "Kentucky"},
        "LA": {"name": "Louisiana"},
        "ME": {"name": "Maine"},
        "MD": {"name": "Maryland"},
        "MA": {"name": "Massachusetts"},
        "MI": {"name": "Michigan"},
        "MN": {"name": "Minnesota"},
        "MS": {"name": "Mississippi"},
        "MO": {"name": "Missouri"},
        "MT": {"name": "Montana"},
        "NE": {"name": "Nebraska"},
        "NV": {"name": "Nevada"},
        "NH": {"name": "New Hampshire"},
        "NJ": {"name": "New Jersey"},
        "NM": {"name": "New Mexico"},
        "NY": {"name": "New York"},
        "NC": {"name": "North Carolina"},
        "ND": {"name": "North Dakota"},
        "OH": {"name": "Ohio"},
        "OK": {"name": "Oklahoma"},
        "OR": {"name": "Oregon"},
        "PA": {"name": "Pennsylvania"},
        "RI": {"name": "Rhode Island"},
        "SC": {"name": "South Carolina"},
        "SD": {"name": "South Dakota"},
        "TN": {"name": "Tennessee"},
        "TX": {"name": "Texas"},
        "UT": {"name": "Utah"},
        "VT": {"name": "Vermont"},
        "VA": {"name": "Virginia"},
        "WA": {"name": "Washington"},
        "WV": {"name": "West Virginia"},
        "WI": {"name": "Wisconsin"},
        "WY": {"name": "Wyoming"},
        "DC": {"name": "District of Columbia"},
    }

    NEWS_SOURCES: dict = {
        "chicago": [
            {"name": "Chicago Sun-Times", "feed_url": "https://chicago.suntimes.com/rss/index.xml"},
            {"name": "Block Club Chicago", "feed_url": "https://blockclubchicago.org/feed/"},
        ],
        "detroit": [
            {"name": "Detroit Free Press", "feed_url": "https://www.freep.com/arcio/rss/"},
        ],
        "seattle": [
            {"name": "The Urbanist", "feed_url": "https://www.theurbanist.org/feed/"},
        ],
        "minneapolismn": [
            {"name": "Minnesota Reformer", "feed_url": "https://minnesotareformer.com/feed/"},
        ],
    }

    model_config = {"env_file": ("../.env", ".env"), "extra": "ignore"}


settings = Settings()
