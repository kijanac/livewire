import json
import logging
import time

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.database import SessionLocal
from app.models import Bill

logger = logging.getLogger(__name__)

# Module-level cache
_index: "SimilarityIndex | None" = None
_index_built_at: float = 0
INDEX_TTL_SECONDS = 3600  # rebuild after 1 hour


class SimilarityIndex:
    """TF-IDF vector index over all bill titles + topics for similarity search."""

    def __init__(self, bill_ids: list[int], texts: list[str]) -> None:
        self.bill_ids = bill_ids
        self.id_to_idx = {bid: i for i, bid in enumerate(bill_ids)}
        self.vectorizer = TfidfVectorizer(
            max_features=10000,
            stop_words="english",
            ngram_range=(1, 2),
            sublinear_tf=True,
        )
        self.matrix = self.vectorizer.fit_transform(texts)
        logger.info(
            "Similarity index built",
            extra={
                "event": "similarity_index_built",
                "num_bills": len(bill_ids),
                "vocab_size": len(self.vectorizer.vocabulary_),
            },
        )

    def find_similar(
        self, bill_id: int, n: int = 5, exclude_same_city: str | None = None
    ) -> list[tuple[int, float]]:
        """Return top-N similar bill IDs with scores, excluding the bill itself."""
        idx = self.id_to_idx.get(bill_id)
        if idx is None:
            return []

        bill_vector = self.matrix[idx]
        scores = cosine_similarity(bill_vector, self.matrix).flatten()

        # Zero out self
        scores[idx] = 0.0

        # Get top N+extra indices (we may filter some out)
        top_count = min(n * 3, len(scores))
        top_indices = scores.argsort()[::-1][:top_count]

        results = []
        for i in top_indices:
            if scores[i] <= 0.0:
                break
            results.append((self.bill_ids[i], float(scores[i])))
            if len(results) >= n:
                break

        return results


def _build_index() -> SimilarityIndex:
    """Build a fresh similarity index from all bills in the database."""
    session = SessionLocal()
    try:
        bills = session.query(Bill.id, Bill.title, Bill.topics, Bill.city_name).all()

        bill_ids = []
        texts = []
        for bill_id, title, topics_json, city_name in bills:
            # Combine title + topics + city for richer embeddings
            topics_str = ""
            if topics_json:
                try:
                    topics_list = json.loads(topics_json)
                    topics_str = " ".join(t.replace("_", " ") for t in topics_list)
                except (ValueError, TypeError):
                    pass
            text = f"{title} {topics_str} {city_name}"
            bill_ids.append(bill_id)
            texts.append(text)

        return SimilarityIndex(bill_ids, texts)
    finally:
        session.close()


def get_index() -> SimilarityIndex:
    """Get the cached similarity index, rebuilding if stale."""
    global _index, _index_built_at

    now = time.time()
    if _index is None or (now - _index_built_at) > INDEX_TTL_SECONDS:
        _index = _build_index()
        _index_built_at = now

    return _index


def find_similar_bills(bill_id: int, n: int = 5) -> list[tuple[int, float]]:
    """Find N most similar bills by TF-IDF cosine similarity."""
    index = get_index()
    return index.find_similar(bill_id, n=n)


def cluster_bills(
    bill_ids: list[int] | None = None,
    distance_threshold: float = 0.7,
) -> list[dict]:
    """Cluster bills by TF-IDF similarity. Returns list of cluster dicts.

    Each cluster: {"label": str, "bill_ids": list[int], "top_terms": list[str]}
    Only returns clusters spanning 2+ unique cities.
    """
    from sklearn.cluster import AgglomerativeClustering

    index = get_index()

    if bill_ids:
        # Map to matrix indices
        indices = [index.id_to_idx[bid] for bid in bill_ids if bid in index.id_to_idx]
    else:
        indices = list(range(len(index.bill_ids)))

    if len(indices) < 2:
        return []

    sub_matrix = index.matrix[indices]

    # Cosine distance = 1 - cosine_similarity
    sim_matrix = cosine_similarity(sub_matrix)
    distance_matrix = 1.0 - sim_matrix

    clustering = AgglomerativeClustering(
        n_clusters=None,
        distance_threshold=distance_threshold,
        metric="precomputed",
        linkage="average",
    )
    labels = clustering.fit_predict(distance_matrix)

    # Group bills by cluster label
    from collections import defaultdict

    clusters_map: dict[int, list[int]] = defaultdict(list)
    for i, label in enumerate(labels):
        clusters_map[label].append(indices[i])

    # Build cluster info
    feature_names = index.vectorizer.get_feature_names_out()
    results = []

    for cluster_indices in clusters_map.values():
        cluster_bill_ids = [index.bill_ids[i] for i in cluster_indices]

        if len(cluster_bill_ids) < 2:
            continue

        # Extract top terms for this cluster
        cluster_vector = sub_matrix[[indices.index(i) for i in cluster_indices if i in indices]].mean(axis=0)
        cluster_array = cluster_vector.A1 if hasattr(cluster_vector, "A1") else cluster_vector
        top_term_indices = cluster_array.argsort()[::-1][:5]
        top_terms = [feature_names[j] for j in top_term_indices if cluster_array[j] > 0]

        # Generate a readable label from top 2-3 terms
        label = " / ".join(t.replace("_", " ").title() for t in top_terms[:3])

        results.append({
            "label": label,
            "bill_ids": cluster_bill_ids,
            "top_terms": list(top_terms),
        })

    # Sort by cluster size descending
    results.sort(key=lambda c: len(c["bill_ids"]), reverse=True)

    logger.info(
        "Bill clustering completed",
        extra={
            "event": "clustering_completed",
            "input_bills": len(indices),
            "clusters_found": len(results),
        },
    )

    return results
