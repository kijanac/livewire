import heapq
import json
import logging
import time

import httpx
import numpy as np

from app.config import settings
from app.database import SessionLocal
from app.models import Bill, BillEmbedding

logger = logging.getLogger(__name__)

EMBEDDING_MODEL = "nvidia/llama-nemotron-embed-vl-1b-v2:free"
EMBEDDING_BATCH_SIZE = 50


def _load_vector(emb_bytes: bytes | None, emb_json: str | None) -> np.ndarray | None:
    """Decode an embedding row, preferring bytes and falling back to JSON."""
    if emb_bytes:
        return np.frombuffer(emb_bytes, dtype=np.float32)
    if emb_json:
        try:
            return np.array(json.loads(emb_json), dtype=np.float32)
        except (ValueError, TypeError):
            return None
    return None


def _call_embeddings_api(texts: list[str]) -> list[list[float]]:
    """Call OpenRouter embeddings API. Returns list of embedding vectors."""
    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": EMBEDDING_MODEL,
        "input": texts,
    }
    with httpx.Client(timeout=30.0) as client:
        response = client.post(
            "https://openrouter.ai/api/v1/embeddings",
            json=payload,
            headers=headers,
        )
        response.raise_for_status()
        data = response.json()
        # Sort by index to preserve order
        sorted_data = sorted(data["data"], key=lambda x: x["index"])
        return [item["embedding"] for item in sorted_data]


def embed_unembedded_bills(session=None) -> int:
    """Generate and store embeddings for bills that don't have them yet."""
    if not settings.OPENROUTER_API_KEY:
        return 0

    own_session = session is None
    if own_session:
        session = SessionLocal()

    try:
        # Find bills without embeddings
        embedded_ids = {
            row[0]
            for row in session.query(BillEmbedding.bill_id).all()
        }
        unembedded = (
            session.query(Bill.id, Bill.title, Bill.topics, Bill.city_name)
            .filter(Bill.id.notin_(embedded_ids) if embedded_ids else True)
            .all()
        )

        if not unembedded:
            return 0

        total = 0
        for i in range(0, len(unembedded), EMBEDDING_BATCH_SIZE):
            batch = unembedded[i : i + EMBEDDING_BATCH_SIZE]
            texts = []
            for bill_id, title, topics_json, city_name in batch:
                topics_str = ""
                if topics_json:
                    try:
                        topics_str = " ".join(
                            t.replace("_", " ") for t in json.loads(topics_json)
                        )
                    except (ValueError, TypeError):
                        pass
                texts.append(f"{title} {topics_str} {city_name}")

            try:
                embeddings = _call_embeddings_api(texts)
                for (bill_id, _, _, _), emb in zip(batch, embeddings):
                    arr = np.asarray(emb, dtype=np.float32)
                    session.add(
                        BillEmbedding(
                            bill_id=bill_id,
                            embedding_json=None,
                            embedding_bytes=arr.tobytes(),
                        )
                    )
                session.commit()
                total += len(embeddings)
                time.sleep(0.2)
            except (httpx.HTTPError, json.JSONDecodeError, KeyError) as exc:
                logger.exception(
                    "embedding_batch_failed",
                    extra={
                        "error": str(exc)[:200],
                        "batch_start": i,
                    },
                )
                session.rollback()

        logger.info(
            "embeddings_generated",
            extra={"count": total},
        )
        return total
    finally:
        if own_session:
            session.close()


def find_similar_bills(bill_id: int, n: int = 5) -> list[tuple[int, float]]:
    """Find N most similar bills. Uses pre-computed cache when available,
    falls back to full embedding scan otherwise.
    """
    session = SessionLocal()
    try:
        target = (
            session.query(BillEmbedding)
            .filter(BillEmbedding.bill_id == bill_id)
            .first()
        )
        if not target:
            return []

        # Try pre-computed cache first
        if target.similar_json:
            try:
                cached = json.loads(target.similar_json)
                return [(bid, score) for bid, score in cached[:n]]
            except (ValueError, TypeError):
                pass

        # Fall back to full scan
        return _scan_similar(session, target, n)
    finally:
        session.close()


def _scan_similar(
    session, target: BillEmbedding, n: int,
) -> list[tuple[int, float]]:
    """Full embedding scan for similar bills. Used as fallback and for pre-computation."""
    CHUNK_SIZE = 200
    target_vec = _load_vector(target.embedding_bytes, target.embedding_json)
    if target_vec is None:
        return []
    target_norm = np.linalg.norm(target_vec)
    if target_norm == 0:
        return []
    target_vec = target_vec / target_norm

    base_query = (
        session.query(
            BillEmbedding.bill_id,
            BillEmbedding.embedding_bytes,
            BillEmbedding.embedding_json,
        )
        .filter(BillEmbedding.bill_id != target.bill_id)
        .order_by(BillEmbedding.bill_id)
    )
    top_n: list[tuple[float, int]] = []
    offset = 0

    while True:
        chunk = base_query.limit(CHUNK_SIZE).offset(offset).all()
        if not chunk:
            break

        for other_id, other_bytes, other_json in chunk:
            other_vec = _load_vector(other_bytes, other_json)
            if other_vec is None:
                continue
            other_norm = np.linalg.norm(other_vec)
            if other_norm == 0:
                continue
            similarity = float(np.dot(target_vec, other_vec / other_norm))
            if similarity > settings.SIMILAR_THRESHOLD:
                if len(top_n) < n:
                    heapq.heappush(top_n, (similarity, other_id))
                elif similarity > top_n[0][0]:
                    heapq.heapreplace(top_n, (similarity, other_id))

        offset += CHUNK_SIZE

    return [(bid, score) for score, bid in sorted(top_n, reverse=True)]


def compute_all_similar(session=None) -> int:
    """Pre-compute similar bills for all embeddings missing a cache.
    Call after embed_unembedded_bills() in the ingestion pipeline.
    Processes in batches to stay within memory limits.
    """
    own_session = session is None
    if own_session:
        session = SessionLocal()

    try:
        count = 0
        while True:
            batch = (
                session.query(BillEmbedding)
                .filter(BillEmbedding.similar_json.is_(None))
                .limit(settings.SIMILAR_BATCH)
                .all()
            )
            if not batch:
                break

            for emb in batch:
                try:
                    similar = _scan_similar(session, emb, settings.SIMILAR_N)
                    emb.similar_json = json.dumps(similar)
                    count += 1
                except (json.JSONDecodeError, KeyError, ValueError) as exc:
                    logger.exception(
                        "similar_computation_failed",
                        extra={"bill_id": emb.bill_id, "error": str(exc)[:200]},
                    )

            session.commit()
            # Evict processed objects from the session identity map
            for emb in batch:
                session.expire(emb)
            del batch
            time.sleep(0.1)

        logger.info(
            "similar_precomputed",
            extra={"count": count},
        )
        return count
    finally:
        if own_session:
            session.close()


MAX_CLUSTER_BILLS = 500


def cluster_bills(
    bill_ids: list[int] | None = None,
    distance_threshold: float = 0.35,
) -> list[dict]:
    """Cluster bills by embedding similarity. Returns list of cluster dicts.

    Uses simple greedy clustering: pick the most connected unassigned bill,
    gather all similar bills above threshold into a cluster. No dense matrix needed.
    Capped at MAX_CLUSTER_BILLS (most recent) to stay within memory limits.
    """
    session = SessionLocal()
    try:
        query = session.query(
            BillEmbedding.bill_id,
            BillEmbedding.embedding_bytes,
            BillEmbedding.embedding_json,
        )
        if bill_ids:
            if len(bill_ids) > MAX_CLUSTER_BILLS:
                bill_ids = sorted(bill_ids, reverse=True)[:MAX_CLUSTER_BILLS]
            query = query.filter(BillEmbedding.bill_id.in_(bill_ids))
        else:
            query = query.order_by(BillEmbedding.bill_id.desc()).limit(MAX_CLUSTER_BILLS)
        rows = query.all()

        if len(rows) < 2:
            return []

        ids = []
        vecs = []
        for bid, emb_bytes, emb_json in rows:
            vec = _load_vector(emb_bytes, emb_json)
            if vec is None:
                continue
            norm = np.linalg.norm(vec)
            if norm > 0:
                ids.append(bid)
                vecs.append(vec / norm)

        if len(ids) < 2:
            return []

        mat = np.stack(vecs)  # (N, dim) — N × dim, not N × N
        assigned = set()
        clusters = []

        for i in range(len(ids)):
            if ids[i] in assigned:
                continue

            # Find all bills similar to this one
            sims = mat @ mat[i]  # (N,) dot products — O(N×dim), not O(N²)
            cluster_indices = [
                j for j in range(len(ids))
                if sims[j] >= distance_threshold and ids[j] not in assigned
            ]

            if len(cluster_indices) < 2:
                assigned.add(ids[i])
                continue

            cluster_bill_ids = [ids[j] for j in cluster_indices]
            for bid in cluster_bill_ids:
                assigned.add(bid)

            # Extract label from centroid
            centroid = mat[cluster_indices].mean(axis=0)
            # Use bill titles for the label (will be replaced by LLM in the router)
            clusters.append({
                "label": f"Cluster {len(clusters) + 1}",
                "bill_ids": cluster_bill_ids,
                "top_terms": [],
            })

        clusters.sort(key=lambda c: len(c["bill_ids"]), reverse=True)

        logger.info(
            "clustering_completed",
            extra={
                "input_bills": len(ids),
                "clusters_found": len(clusters),
            },
        )
        return clusters
    finally:
        session.close()
