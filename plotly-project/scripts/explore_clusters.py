"""Cluster review embeddings and inspect what each cluster actually contains.

This is an exploratory companion to the dimensionality-reduction pipeline. It
does NOT change the reduction; it only helps you interpret it. Three things
happen here:

1. Clustering -- preferably on the original embeddings (reduced with PCA),
   NOT on the 2D coordinates. Clustering on a t-SNE/UMAP/PaCMAP layout is a
   known anti-pattern: those layouts are optimised for looks, so clusters
   found there can be projection artefacts. PCA -> HDBSCAN on the real
   embeddings reflects the actual structure. If you do not pass --embeddings
   the script falls back to clustering the 2D coords and says so.

2. Visualisation -- the 2D coordinates are plotted and coloured by the cluster
   labels computed in step 1, so you see the *real* groups laid over the map.

3. Reading the reviews -- if you pass --reviews, the script prints a few
   example review texts per cluster, so you can tell what each island is
   about (a product type, templated text, a language, etc.).

Data prerequisite
-----------------
The coords_*.csv files only carry point_id / x / y / rating / parent_asin.
To cluster on embeddings or read review text you need the matching artifacts
produced by ``prepare_embeddings(n)`` (see src/embeddings.py):
    reviews_<n>.csv   and   embeddings_<n>.npy
``point_id`` in the coords file is the row index into both of those files.

Example
-------
    python scripts/explore_clusters.py \
        dim_reduction/results_small/coordinates/coords_pacmap_5000.csv \
        --embeddings dim_reduction/results_small/data/embeddings_5000.npy \
        --reviews    dim_reduction/results_small/data/reviews_5000.csv \
        --min-cluster-size 30 --samples 5
"""
from __future__ import annotations

import argparse
import sys
import textwrap
from pathlib import Path

import numpy as np
import pandas as pd

# Review text can contain emoji; a cp1250/cp1252 Windows console cannot encode
# them and would crash on print. Fall back to replacing unencodable chars.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

# Pretty names for the 2D projection method (matches config.METHOD_LABELS).
METHOD_LABELS = {"pca": "PCA", "umap": "UMAP", "pacmap": "PaCMAP", "fitsne": "FIt-SNE"}


def projection_label(coords: pd.DataFrame, fallback: str) -> str:
    """Human-readable name of the 2D method that drew this layout."""
    if "method" in coords.columns and len(coords):
        method = str(coords["method"].iloc[0]).lower()
        return METHOD_LABELS.get(method, method)
    return fallback


def cluster_points(
    coords: pd.DataFrame,
    embeddings: np.ndarray | None,
    min_cluster_size: int,
    pca_dim: int,
) -> tuple[np.ndarray, str]:
    """Return (labels, description). Clusters embeddings if given, else 2D."""
    import hdbscan

    if embeddings is not None:
        # Align embeddings to the rows present in coords via point_id, then
        # compress with PCA -- HDBSCAN struggles in very high dimensions.
        from sklearn.decomposition import PCA

        idx = coords["point_id"].to_numpy()
        vecs = embeddings[idx]
        n_comp = min(pca_dim, vecs.shape[1], vecs.shape[0] - 1)
        vecs = PCA(n_components=n_comp, random_state=42).fit_transform(vecs)
        source = f"embeddings (PCA->{n_comp}D)"
    else:
        vecs = coords[["x", "y"]].to_numpy()
        source = "2D coordinates (fallback -- weaker; pass --embeddings)"

    labels = hdbscan.HDBSCAN(min_cluster_size=min_cluster_size).fit_predict(vecs)
    return labels, source


def plot_clusters(coords: pd.DataFrame, out_path: Path, title: str) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(8, 6))
    scatter = ax.scatter(
        coords["x"], coords["y"], c=coords["cluster"],
        cmap="tab20", s=8, alpha=0.7, linewidths=0,
    )
    fig.colorbar(scatter, ax=ax, label="Cluster (-1 = noise)")
    ax.set_title(title)
    ax.set_xlabel("Component 1")
    ax.set_ylabel("Component 2")
    ax.grid(True, alpha=0.2)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(out_path, dpi=180)
    plt.close(fig)
    print(f"Saved cluster plot: {out_path}")


def print_cluster_texts(
    coords: pd.DataFrame, reviews: pd.DataFrame, samples: int, width: int = 100
) -> None:
    sizes = coords["cluster"].value_counts().sort_values(ascending=False)
    for cluster_id, size in sizes.items():
        head = "NOISE (-1)" if cluster_id == -1 else f"CLUSTER {cluster_id}"
        print(f"\n{'='*70}\n{head}  --  {size} points")
        members = coords[coords["cluster"] == cluster_id]
        take = members.sample(min(samples, len(members)), random_state=42)
        for _, row in take.iterrows():
            text = str(reviews.iloc[int(row["point_id"])]["text"])
            snippet = textwrap.shorten(text, width=width, placeholder=" ...")
            print(f"  [{row['parent_asin']} | {row['rating']}*] {snippet}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("coords", type=Path, help="coords_<method>_<n>.csv")
    parser.add_argument("--embeddings", type=Path, default=None,
                        help="embeddings_<n>.npy -- cluster on these (recommended).")
    parser.add_argument("--reviews", type=Path, default=None,
                        help="reviews_<n>.csv -- to print review text per cluster.")
    parser.add_argument("--min-cluster-size", type=int, default=30)
    parser.add_argument("--pca-dim", type=int, default=50)
    parser.add_argument("--samples", type=int, default=5,
                        help="Example reviews to print per cluster (default: 5).")
    parser.add_argument("--no-plot", action="store_true")
    args = parser.parse_args()

    coords = pd.read_csv(args.coords)

    embeddings = None
    if args.embeddings is not None:
        if not args.embeddings.exists():
            raise FileNotFoundError(
                f"Embeddings not found: {args.embeddings}. Generate them first with "
                "prepare_embeddings(n) (creates embeddings_<n>.npy)."
            )
        embeddings = np.load(args.embeddings)

    labels, source = cluster_points(
        coords, embeddings, args.min_cluster_size, args.pca_dim
    )
    coords["cluster"] = labels

    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    n_noise = int((labels == -1).sum())
    print(f"Loaded {len(coords)} points from {args.coords}")
    print(f"Clustered on: {source}")
    print(f"Clusters found: {n_clusters} | noise points: {n_noise} "
          f"({n_noise / len(coords):.1%})")

    labeled_path = args.coords.with_name(f"{args.coords.stem}_labeled.csv")
    coords.to_csv(labeled_path, index=False)
    print(f"Saved labeled coords: {labeled_path}")

    if not args.no_plot:
        plot_path = args.coords.with_name(f"{args.coords.stem}_clusters_real.png")
        proj = projection_label(coords, fallback=args.coords.stem)
        plot_clusters(coords, plot_path, title=f"{proj} layout - clusters from {source}")

    if args.reviews is not None:
        if not args.reviews.exists():
            raise FileNotFoundError(
                f"Reviews not found: {args.reviews}. Generate them first with "
                "prepare_embeddings(n) (creates reviews_<n>.csv)."
            )
        reviews = pd.read_csv(args.reviews)
        print_cluster_texts(coords, reviews, args.samples)
    else:
        print("\n(Tip: pass --reviews reviews_<n>.csv to print example texts per cluster.)")


if __name__ == "__main__":
    main()
