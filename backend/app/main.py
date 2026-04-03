import gc
import logging
import os
import threading
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import SessionLocal, init_db
from app.ingesters.legistar import LegistarIngester
from app.routers import bills, collections, stories

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

    # Generate embeddings for any new bills, then pre-compute similar bills
    if settings.OPENROUTER_API_KEY:
        from app.similarity import compute_all_similar, embed_unembedded_bills

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

        gc.collect()

        try:
            precomputed = compute_all_similar()
            logger.info(
                "Post-ingestion similar bills pre-computed",
                extra={
                    "event": "post_ingestion_similar_completed",
                    "bills_precomputed": precomputed,
                },
            )
        except Exception:
            logger.exception(
                "Post-ingestion similar computation failed",
                extra={"event": "post_ingestion_similar_failed"},
            )

        gc.collect()

    # --- Story ingestion pipeline ---
    _ingest_stories()


def _sync_story_sources(session: SessionLocal) -> None:
    """Ensure configured NEWS_SOURCES exist as StorySource rows."""
    from app.models import StorySource

    for city_key, feeds in settings.NEWS_SOURCES.items():
        city_config = settings.CITIES.get(city_key)
        if not city_config:
            continue
        for feed in feeds:
            exists = (
                session.query(StorySource.id)
                .filter(StorySource.feed_url == feed["feed_url"])
                .first()
            )
            if not exists:
                session.add(StorySource(
                    city=city_key,
                    city_name=city_config["name"],
                    state=city_config["state"],
                    name=feed["name"],
                    feed_url=feed["feed_url"],
                ))
    session.commit()


_STORY_RETENTION_DAYS = 90


def _ingest_stories() -> None:
    """Fetch RSS feeds, triage, enrich relevant stories, and prune old ones."""
    from app.ingesters.rss import RSSIngester
    from app.models import Story, StorySource

    session = SessionLocal()
    try:
        _sync_story_sources(session)

        sources = session.query(StorySource).filter(StorySource.is_active.is_(True)).all()
        total_added = 0
        for source in sources:
            ingester = RSSIngester(source)
            added, _ = ingester.ingest(session)
            total_added += added

        logger.info(
            "Story RSS ingestion completed",
            extra={"event": "story_rss_ingestion_completed", "stories_added": total_added},
        )
    except Exception:
        logger.exception(
            "Story RSS ingestion failed",
            extra={"event": "story_rss_ingestion_failed"},
        )
    finally:
        session.close()

    gc.collect()

    # Triage + enrich
    if settings.OPENROUTER_API_KEY:
        from app.story_classifier import enrich_all_stories, triage_all_stories

        session = SessionLocal()
        try:
            triaged = triage_all_stories(session)
            logger.info(
                "Story triage completed",
                extra={"event": "story_triage_pipeline_completed", "stories_triaged": triaged},
            )
        except Exception:
            logger.exception(
                "Story triage failed",
                extra={"event": "story_triage_pipeline_failed"},
            )
        finally:
            session.close()

        session = SessionLocal()
        try:
            enriched = enrich_all_stories(session)
            logger.info(
                "Story enrichment completed",
                extra={"event": "story_enrichment_pipeline_completed", "stories_enriched": enriched},
            )
        except Exception:
            logger.exception(
                "Story enrichment failed",
                extra={"event": "story_enrichment_pipeline_failed"},
            )
        finally:
            session.close()

        gc.collect()

    # Prune old stories
    session = SessionLocal()
    try:
        cutoff = datetime.now(tz=timezone.utc) - timedelta(days=_STORY_RETENTION_DAYS)
        deleted = session.query(Story).filter(Story.created_at < cutoff).delete()
        session.commit()
        if deleted:
            logger.info(
                "Old stories pruned",
                extra={"event": "story_retention_pruned", "deleted": deleted},
            )
    except Exception:
        logger.exception(
            "Story retention pruning failed",
            extra={"event": "story_retention_failed"},
        )
    finally:
        session.close()


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


app = FastAPI(title="Livewire", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(bills.router)
app.include_router(collections.router)
app.include_router(stories.router)

# Mount static files for frontend if the directory exists
static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
if os.path.isdir(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
