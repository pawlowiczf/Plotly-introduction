"""End-to-end clustering experiment on the full ~200k review parquet.

Pipeline:
  1. Load data/reviews_clean.parquet (text + metadata, no embeddings).
  2. Encode the review texts with the project SentenceTransformer model and
     cache the vectors to disk (the expensive step -- saved first so a later
     crash never wastes it).
  3. Cluster the embeddings: PCA -> HDBSCAN. We cluster the real embeddings,
     not a 2D projection (clustering a UMAP/PaCMAP layout is an anti-pattern).
  4. Report: cluster sizes + mean rating, a few example reviews per cluster,
     and the most anomalous reviews via HDBSCAN's GLOSH outlier_scores_.
  5. Plot a PCA 2D scatter coloured by cluster (umap/pacmap are broken in this
     env and FIt-SNE is impractical at 200k, so PCA is the fast, honest map).

Outputs land in dim_reduction/results_big/.

Usage:
    python scripts/run_big_experiment.py                 # full run
    python scripts/run_big_experiment.py --limit 20000   # quick smoke test
    python scripts/run_big_experiment.py --min-cluster-size 300
"""
from __future__ import annotations

import argparse
import sys
import textwrap
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import config  # noqa: E402

# Review text contains emoji; avoid crashing a cp1250 Windows console on print.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass


def encode_reviews(texts: list[str], cache_path: Path, batch_size: int) -> np.ndarray:
    """Encode texts to embeddings, caching the result to cache_path."""
    if cache_path.exists():
        emb = np.load(cache_path)
        if len(emb) == len(texts):
            print(f"Reusing cached embeddings: {cache_path} {emb.shape}")
            return emb
        print(f"Cache size {len(emb)} != {len(texts)} texts; re-encoding.")

    from sentence_transformers import SentenceTransformer

    print(f"Encoding {len(texts)} texts with {config.MODEL_NAME} (batch={batch_size})")
    model = SentenceTransformer(config.MODEL_NAME)
    start = time.perf_counter()
    emb = model.encode(
        texts, batch_size=batch_size, show_progress_bar=True, convert_to_numpy=True
    ).astype(np.float32)
    print(f"Encoded in {time.perf_counter() - start:.0f}s -> {emb.shape}")
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    np.save(cache_path, emb)
    print(f"Saved embeddings: {cache_path}")
    return emb


def cluster(embeddings: np.ndarray, pca_dim: int, min_cluster_size: int):
    """PCA -> HDBSCAN. Returns (labels, outlier_scores, pca_2d)."""
    from sklearn.decomposition import PCA
    import hdbscan

    n_comp = min(pca_dim, embeddings.shape[1])
    print(f"PCA -> {n_comp}D")
    pca = PCA(n_components=n_comp, random_state=42)
    reduced = pca.fit_transform(embeddings)

    print(f"HDBSCAN (min_cluster_size={min_cluster_size}) on {reduced.shape[0]} points")
    start = time.perf_counter()
    clusterer = hdbscan.HDBSCAN(min_cluster_size=min_cluster_size, core_dist_n_jobs=-1)
    clusterer.fit(reduced)
    print(f"Clustered in {time.perf_counter() - start:.0f}s")

    # A fast, honest 2D map: first two PCA components (reuse the same PCA).
    pca_2d = reduced[:, :2]
    return clusterer.labels_, clusterer.outlier_scores_, pca_2d


def summarize(df: pd.DataFrame) -> pd.DataFrame:
    summary = (
        df.groupby("cluster")
        .agg(size=("text", "size"), mean_rating=("rating", "mean"))
        .sort_values("size", ascending=False)
    )
    return summary


def print_cluster_texts(df: pd.DataFrame, samples: int, width: int = 110) -> None:
    for cluster_id, size in df["cluster"].value_counts().items():
        head = "NOISE (-1)" if cluster_id == -1 else f"CLUSTER {cluster_id}"
        mean_r = df.loc[df["cluster"] == cluster_id, "rating"].mean()
        print(f"\n{'='*72}\n{head}  --  {size} reviews  |  mean rating {mean_r:.2f}")
        take = df[df["cluster"] == cluster_id].sample(min(samples, size), random_state=42)
        for _, row in take.iterrows():
            snippet = textwrap.shorten(str(row["text"]), width=width, placeholder=" ...")
            print(f"  [{row['parent_asin']} | {row['rating']}*] {snippet}")


def print_outliers(df: pd.DataFrame, top: int, width: int = 110) -> None:
    print(f"\n{'#'*72}\nTOP {top} OUTLIERS (HDBSCAN GLOSH outlier_score)\n{'#'*72}")
    out = df.sort_values("outlier_score", ascending=False).head(top)
    for _, row in out.iterrows():
        snippet = textwrap.shorten(str(row["text"]), width=width, placeholder=" ...")
        print(f"  [score {row['outlier_score']:.3f} | {row['parent_asin']} | "
              f"{row['rating']}* | cl {row['cluster']}] {snippet}")


def plot(df: pd.DataFrame, out_path: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(9, 7))
    sc = ax.scatter(df["x"], df["y"], c=df["cluster"], cmap="tab20",
                    s=3, alpha=0.5, linewidths=0)
    fig.colorbar(sc, ax=ax, label="Cluster (-1 = noise)")
    ax.set_title(f"PCA(2D) layout of {len(df)} reviews - clusters from embeddings")
    ax.set_xlabel("PC 1")
    ax.set_ylabel("PC 2")
    ax.grid(True, alpha=0.2)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(out_path, dpi=160)
    plt.close(fig)
    print(f"Saved plot: {out_path}")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--parquet", type=Path, default=ROOT / "data" / "reviews_clean.parquet")
    p.add_argument("--out-dir", type=Path, default=ROOT / "dim_reduction" / "results_big")
    p.add_argument("--limit", type=int, default=None, help="Use only the first N rows.")
    p.add_argument("--batch-size", type=int, default=64)
    p.add_argument("--pca-dim", type=int, default=50)
    p.add_argument("--min-cluster-size", type=int, default=200)
    p.add_argument("--samples", type=int, default=4, help="Example reviews per cluster.")
    p.add_argument("--top-outliers", type=int, default=25)
    args = p.parse_args()

    df = pd.read_parquet(args.parquet)
    if args.limit:
        df = df.head(args.limit)
    df = df.reset_index(drop=True)
    print(f"Loaded {len(df)} reviews from {args.parquet}")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    cache = args.parquet.with_name(f"embeddings_{args.parquet.stem}_{len(df)}.npy")
    embeddings = encode_reviews(df["text"].fillna("").tolist(), cache, args.batch_size)

    labels, outlier_scores, pca_2d = cluster(embeddings, args.pca_dim, args.min_cluster_size)
    df["cluster"] = labels
    df["outlier_score"] = outlier_scores
    df["x"], df["y"] = pca_2d[:, 0], pca_2d[:, 1]

    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    n_noise = int((labels == -1).sum())
    print(f"\nClusters: {n_clusters} | noise: {n_noise} ({n_noise/len(df):.1%})")

    summary = summarize(df)
    print("\n=== cluster summary (size, mean rating) ===")
    print(summary.to_string())

    keep = ["point_id", "cluster", "outlier_score", "rating", "parent_asin", "asin", "x", "y"]
    df["point_id"] = df.index
    df[keep].to_csv(args.out_dir / "clusters_labeled.csv", index=False)
    summary.to_csv(args.out_dir / "cluster_summary.csv")
    print(f"Saved: {args.out_dir / 'clusters_labeled.csv'}")

    plot(df, args.out_dir / "clusters_pca2d.png")
    print_cluster_texts(df, args.samples)
    print_outliers(df, args.top_outliers)
    print("\n=== DONE ===")


if __name__ == "__main__":
    main()
