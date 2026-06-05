from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

import config
from src.text import normalize_text


@dataclass(frozen=True)
class EmbeddingArtifacts:
    reviews_path: Path
    embeddings_path: Path
    n_samples: int
    elapsed_seconds: float | None = None


def load_review_sample(
    n_samples: int,
    dataset_name: str = config.DATASET_NAME,
    subset: str = config.SUBSET,
) -> pd.DataFrame:
    """Load exactly n_samples non-empty review texts from Hugging Face."""
    try:
        from datasets import load_dataset
    except ImportError as exc:
        raise RuntimeError("Install project dependencies before loading reviews.") from exc

    dataset = load_dataset(
        dataset_name,
        subset,
        streaming=True,
        trust_remote_code=True,
    )

    rows: list[dict[str, object]] = []
    for row in dataset["full"]:
        text = normalize_text(row.get("text"))
        if not text:
            continue

        rows.append(
            {
                "text": text,
                "title": normalize_text(row.get("title")),
                "rating": row.get("rating"),
                "asin": row.get("asin"),
                "parent_asin": row.get("parent_asin"),
                "user_id": row.get("user_id"),
                "timestamp": row.get("timestamp"),
                "helpful_vote": row.get("helpful_vote"),
                "verified_purchase": row.get("verified_purchase"),
            }
        )

        if len(rows) >= n_samples:
            break

        if len(rows) % 1_000 == 0:
            print(f"Loaded {len(rows)} non-empty reviews")

    if len(rows) < n_samples:
        raise RuntimeError(f"Loaded only {len(rows)} reviews, expected {n_samples}")

    reviews = pd.DataFrame(rows)
    reviews["text_len"] = reviews["text"].str.len()
    reviews["title_len"] = reviews["title"].str.len()
    return reviews


def prepare_embeddings(
    n_samples: int,
    output_dir: Path = config.SMALL_DATA_DIR,
    model_name: str = config.MODEL_NAME,
    batch_size: int = config.SMALL_BATCH_SIZE,
    device: str | None = None,
    force: bool = False,
) -> EmbeddingArtifacts:
    """Create or reuse local review CSV and SentenceTransformer embeddings."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    reviews_path = output_dir / f"reviews_{n_samples}.csv"
    embeddings_path = output_dir / f"embeddings_{n_samples}.npy"

    if reviews_path.exists() and embeddings_path.exists() and not force:
        print(f"Reusing reviews: {reviews_path}")
        print(f"Reusing embeddings: {embeddings_path}")
        return EmbeddingArtifacts(reviews_path, embeddings_path, n_samples)

    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise RuntimeError(
            "Could not import sentence-transformers. Install the pinned project "
            "dependencies with: python -m pip install -r requirements.txt"
        ) from exc

    print(f"Loading {n_samples} reviews from {config.SUBSET}")
    reviews = load_review_sample(n_samples)
    reviews.to_csv(reviews_path, index=False)
    print(f"Saved review sample: {reviews_path}")

    print(f"Encoding texts with {model_name}")
    model = SentenceTransformer(model_name, device=device)

    start = time.perf_counter()
    embeddings = model.encode(
        reviews["text"].tolist(),
        batch_size=batch_size,
        show_progress_bar=True,
        convert_to_numpy=True,
    ).astype(np.float32)
    elapsed = time.perf_counter() - start

    np.save(embeddings_path, embeddings)
    print(f"Saved embeddings: {embeddings_path}")
    print(f"Embedding shape: {embeddings.shape}")
    print(f"Encoding time_seconds: {elapsed:.2f}")

    return EmbeddingArtifacts(reviews_path, embeddings_path, n_samples, elapsed)
