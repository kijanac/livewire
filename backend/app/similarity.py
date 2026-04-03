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
                    session.add(
                        BillEmbedding(
                            bill_id=bill_id,
                            embedding_json=json.dumps(emb),
                        )
                    )
                session.commit()
                total += len(embeddings)
                time.sleep(0.2)  # Rate limit courtesy
            except Exception as exc:
                logger.error(
                    "Embedding batch failed",
                    extra={
                        "event": "embedding_batch_failed",
                        "error": str(exc),
                        "batch_start": i,
                    },
                )
                session.rollback()

        logger.info(
            "Embeddings generated",
            extra={"event": "embeddings_generated", "count": total},
        )
        return total
    finally:
        if own_session:
            session.close()


_SIMILAR_N = 10  # pre-compute top 10 for cache


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
    target_vec = np.array(json.loads(target.embedding_json), dtype=np.float32)
    target_norm = np.linalg.norm(target_vec)
    if target_norm == 0:
        return []
    target_vec = target_vec / target_norm

    base_query = (
        session.query(BillEmbedding.bill_id, BillEmbedding.embedding_json)
        .filter(BillEmbedding.bill_id != target.bill_id)
        .order_by(BillEmbedding.bill_id)
    )
    top_n: list[tuple[float, int]] = []
    offset = 0

    while True:
        chunk = base_query.limit(CHUNK_SIZE).offset(offset).all()
        if not chunk:
            break

        for other_id, emb_json in chunk:
            other_vec = np.array(json.loads(emb_json), dtype=np.float32)
            other_norm = np.linalg.norm(other_vec)
            if other_norm == 0:
                continue
            similarity = float(np.dot(target_vec, other_vec / other_norm))
            if similarity > 0.3:
                if len(top_n) < n:
                    heapq.heappush(top_n, (similarity, other_id))
                elif similarity > top_n[0][0]:
                    heapq.heapreplace(top_n, (similarity, other_id))

        offset += CHUNK_SIZE

    return [(bid, score) for score, bid in sorted(top_n, reverse=True)]


_SIMILAR_BATCH = 50


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
                .limit(_SIMILAR_BATCH)
                .all()
            )
            if not batch:
                break

            for emb in batch:
                try:
                    similar = _scan_similar(session, emb, _SIMILAR_N)
                    emb.similar_json = json.dumps(similar)
                    count += 1
                except Exception as exc:
                    logger.error(
                        "Similar computation failed",
                        extra={"event": "similar_computation_failed", "bill_id": emb.bill_id, "error": str(exc)},
                    )

            session.commit()
            # Evict processed objects from the session identity map
            for emb in batch:
                session.expire(emb)
            del batch
            time.sleep(0.1)

        logger.info(
            "Similar bills pre-computed",
            extra={"event": "similar_precomputed", "count": count},
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
        query = session.query(BillEmbedding.bill_id, BillEmbedding.embedding_json)
        if bill_ids:
            if len(bill_ids) > MAX_CLUSTER_BILLS:
                bill_ids = sorted(bill_ids, reverse=True)[:MAX_CLUSTER_BILLS]
            query = query.filter(BillEmbedding.bill_id.in_(bill_ids))
        else:
            query = query.order_by(BillEmbedding.bill_id.desc()).limit(MAX_CLUSTER_BILLS)
        rows = query.all()

        if len(rows) < 2:
            return []

        # Load embeddings into memory
        ids = []
        vecs = []
        for bid, emb_json in rows:
            vec = np.array(json.loads(emb_json), dtype=np.float32)
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
            "Bill clustering completed",
            extra={
                "event": "clustering_completed",
                "input_bills": len(ids),
                "clusters_found": len(clusters),
            },
        )
        return clusters
    finally:
        session.close()
