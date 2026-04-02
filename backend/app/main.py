import logging
import os
import threading
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import SessionLocal, init_db
from app.ingesters.legistar import LegistarIngester
from app.routers import bills, collections

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def run_ingestion_all_cities() -> None:
    """Run Legistar ingestion for every configured city."""
    logger.info(
        "Scheduled ingestion started for all cities",
        extra={"event": "scheduled_ingestion_started"},
    )
    for city_key, city_config in settings.CITIES.items():
        ingester = LegistarIngester(
            city_key=city_key,
            city_config=city_config,
            base_url=settings.LEGISTAR_BASE_URL,
        )
        session = SessionLocal()
        try:
            added, updated = ingester.ingest(session)
            officials_count = ingester.ingest_officials(session)
            logger.info(
                "Scheduled ingestion completed for city",
                extra={
                    "event": "scheduled_ingestion_city_completed",
                    "city": city_key,
                    "bills_added": added,
                    "bills_updated": updated,
                    "officials_synced": officials_count,
                },
            )
        except Exception:
            logger.exception(
                "Scheduled ingestion failed for city",
                extra={
                    "event": "scheduled_ingestion_city_failed",
                    "city": city_key,
                },
            )
        finally:
            session.close()

    logger.info(
        "Scheduled ingestion finished for all cities",
        extra={"event": "scheduled_ingestion_finished"},
    )

    # Run topic tagging on any untagged bills
    if settings.OPENROUTER_API_KEY:
        from app.tagger import tag_all_untagged_bills

        session = SessionLocal()
        try:
            tagged = tag_all_untagged_bills(session)
            logger.info(
                "Post-ingestion tagging completed",
                extra={
                    "event": "post_ingestion_tagging_completed",
                    "bills_tagged": tagged,
                },
            )
        except Exception:
            logger.exception(
                "Post-ingestion tagging failed",
                extra={"event": "post_ingestion_tagging_failed"},
            )
        finally:
            session.close()

    # Generate embeddings for any new bills
    if settings.OPENROUTER_API_KEY:
        from app.similarity import embed_unembedded_bills

        try:
            embedded = embed_unembedded_bills()
            logger.info(
                "Post-ingestion embeddings completed",
                extra={
                    "event": "post_ingestion_embeddings_completed",
                    "bills_embedded": embedded,
                },
            )
        except Exception:
            logger.exception(
                "Post-ingestion embeddings failed",
                extra={"event": "post_ingestion_embeddings_failed"},
            )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup
    init_db()
    logger.info("Database initialized", extra={"event": "database_initialized"})

    scheduler.add_job(
        run_ingestion_all_cities,
        "interval",
        hours=settings.INGEST_INTERVAL_HOURS,
        id="ingest_all_cities",
    )
    scheduler.start()
    logger.info(
        "Scheduler started",
        extra={
            "event": "scheduler_started",
            "interval_hours": settings.INGEST_INTERVAL_HOURS,
        },
    )

    # Run initial ingestion in a background thread so startup is not blocked
    thread = threading.Thread(target=run_ingestion_all_cities, daemon=True)
    thread.start()

    yield

    # Shutdown
    scheduler.shutdown(wait=False)
    logger.info("Scheduler shut down", extra={"event": "scheduler_shutdown"})


app = FastAPI(title="Bill Tracker", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(bills.router)
app.include_router(collections.router)

# Mount static files for frontend if the directory exists
static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
if os.path.isdir(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
