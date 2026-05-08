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
from app.ingesters.legistar_html import HTMLLegistarIngester
from app.ingesters.openstates import OpenStatesIngester
from app.ingesters.rss import RSSIngester
from app.logging_config import setup_logging
from app.middleware import RequestIDMiddleware
from app.models import Story, StorySource
from app.routers import bills, collections, stories
from app.similarity import compute_all_similar, embed_unembedded_bills
from app.story_classifier import enrich_all_stories, triage_all_stories
from app.tagger import tag_all_untagged_bills

setup_logging("INFO")
logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def run_ingestion_all_cities() -> None:
    """Run Legistar ingestion for every configured city.
    Falls back to HTML scraping when the web API is unavailable."""
    logger.info("scheduled_ingestion_started")
    for city_key, city_config in settings.CITIES.items():
        session = SessionLocal()
        try:
            added, updated = _ingest_city(city_key, city_config, session)
            logger.info(
                "scheduled_ingestion_city_completed",
                extra={
                    "city": city_key,
                    "bills_added": added,
                    "bills_updated": updated,
                },
            )
        except Exception:
            logger.exception(
                "scheduled_ingestion_city_failed",
                extra={"city": city_key},
            )
        finally:
            session.close()

    logger.info("scheduled_ingestion_finished")


def _ingest_city(city_key: str, city_config: dict, session) -> tuple[int, int]:
    """Try API ingester first, fall back to HTML scraping on failure."""
    api_ingester = LegistarIngester(
        city_key=city_key,
        city_config=city_config,
        base_url=settings.LEGISTAR_BASE_URL,
    )
    try:
        added, updated = api_ingester.ingest(session)
        api_ingester.ingest_officials(session)
        return added, updated
    except Exception as exc:
        logger.warning(
            "api_ingest_failed_falling_back_to_html",
            extra={"city": city_key, "error": str(exc)[:200]},
        )
        session.rollback()

    html_ingester = HTMLLegistarIngester(
        city_key=city_key, city_config=city_config
    )
    return html_ingester.ingest(session)

    # --- State legislatures via OpenStates ---
    if settings.OPENSTATES_API_KEY:
        for state_code, state_config in settings.STATES.items():
            ingester = OpenStatesIngester(
                state_code=state_code,
                state_name=state_config["name"],
                base_url=settings.OPENSTATES_BASE_URL,
                api_key=settings.OPENSTATES_API_KEY,
            )
            session = SessionLocal()
            try:
                added, updated = ingester.ingest(session)
                logger.info(
                    "scheduled_openstates_state_completed",
                    extra={
                        "state": state_code,
                        "bills_added": added,
                        "bills_updated": updated,
                    },
                )
            except Exception:
                logger.exception(
                    "scheduled_openstates_state_failed",
                    extra={"state": state_code},
                )
            finally:
                session.close()
        gc.collect()

    if settings.OPENROUTER_API_KEY:
        session = SessionLocal()
        try:
            tagged = tag_all_untagged_bills(session)
            logger.info(
                "post_ingestion_tagging_completed",
                extra={"bills_tagged": tagged},
            )
        except Exception:
            logger.exception("post_ingestion_tagging_failed")
        finally:
            session.close()

    if settings.OPENROUTER_API_KEY:
        try:
            embedded = embed_unembedded_bills()
            logger.info(
                "post_ingestion_embeddings_completed",
                extra={"bills_embedded": embedded},
            )
        except Exception:
            logger.exception("post_ingestion_embeddings_failed")

        gc.collect()

        try:
            precomputed = compute_all_similar()
            logger.info(
                "post_ingestion_similar_completed",
                extra={"bills_precomputed": precomputed},
            )
        except Exception:
            logger.exception("post_ingestion_similar_failed")

        gc.collect()

    # --- Story ingestion pipeline ---
    _ingest_stories()


def _sync_story_sources(session: SessionLocal) -> None:
    """Ensure configured NEWS_SOURCES exist as StorySource rows."""
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


def _ingest_stories() -> None:
    """Fetch RSS feeds, triage, enrich relevant stories, and prune old ones."""
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
            "story_rss_ingestion_completed",
            extra={"stories_added": total_added},
        )
    except Exception:
        logger.exception("story_rss_ingestion_failed")
    finally:
        session.close()

    gc.collect()

    if settings.OPENROUTER_API_KEY:
        session = SessionLocal()
        try:
            triaged = triage_all_stories(session)
            logger.info(
                "story_triage_pipeline_completed",
                extra={"stories_triaged": triaged},
            )
        except Exception:
            logger.exception("story_triage_pipeline_failed")
        finally:
            session.close()

        session = SessionLocal()
        try:
            enriched = enrich_all_stories(session)
            logger.info(
                "story_enrichment_pipeline_completed",
                extra={"stories_enriched": enriched},
            )
        except Exception:
            logger.exception("story_enrichment_pipeline_failed")
        finally:
            session.close()

        gc.collect()

    session = SessionLocal()
    try:
        cutoff = datetime.now(tz=timezone.utc) - timedelta(days=settings.STORY_RETENTION_DAYS)
        deleted = session.query(Story).filter(Story.created_at < cutoff).delete()
        session.commit()
        if deleted:
            logger.info(
                "story_retention_pruned",
                extra={"count": deleted},
            )
    except Exception:
        logger.exception("story_retention_failed")
    finally:
        session.close()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    init_db()
    logger.info("database_initialized")

    scheduler.add_job(
        run_ingestion_all_cities,
        "interval",
        hours=settings.INGEST_INTERVAL_HOURS,
        id="ingest_all_cities",
    )
    scheduler.start()
    logger.info(
        "scheduler_started",
        extra={"interval_hours": settings.INGEST_INTERVAL_HOURS},
    )

    thread = threading.Thread(target=run_ingestion_all_cities, daemon=True)
    thread.start()

    yield

    scheduler.shutdown(wait=False)
    logger.info("scheduler_shutdown")


app = FastAPI(title="Livewire", lifespan=lifespan)

app.add_middleware(RequestIDMiddleware)
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
