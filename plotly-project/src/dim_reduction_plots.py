from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

import config


def merge_benchmark_results(
    results_dir: Path = config.SMALL_RESULTS_DIR,
    output: Path | None = None,
) -> pd.DataFrame:
    results_dir = Path(results_dir)
    benchmarks_dir = results_dir / "benchmarks"
    output = Path(output) if output is not None else benchmarks_dir / "results_all.csv"

    paths = sorted(benchmarks_dir.glob("benchmark_*.csv"))
    if not paths:
        raise FileNotFoundError(f"No benchmark_*.csv files found in {benchmarks_dir}")

    results = pd.concat([pd.read_csv(path) for path in paths], ignore_index=True)
    results = results.sort_values(["method", "n_samples"]).reset_index(drop=True)

    output.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(output, index=False)
    print(f"Merged {len(paths)} benchmark files into {output}")
    return results


def plot_runtime(
    results: pd.DataFrame | Path,
    output: Path,
    yscale: str = "linear",
    methods: list[str] | None = None,
) -> Path:
    if isinstance(results, (str, Path)):
        results = pd.read_csv(results)

    methods = methods or config.METHODS
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(8, 5))
    for method in methods:
        data = results[results["method"] == method].sort_values("n_samples")
        if data.empty:
            continue
        label = config.METHOD_LABELS.get(method, method)
        ax.plot(data["n_samples"], data["time_seconds"], marker="o", label=label)

    ax.set_title("Dimensionality reduction runtime")
    ax.set_xlabel("Number of reviews")
    ax.set_ylabel("Time [s]")
    ax.set_yscale(yscale)
    ax.grid(True, alpha=0.3)
    if yscale == "log":
        ax.grid(True, which="minor", alpha=0.15)
    ax.legend(title="Method")

    fig.tight_layout()
    fig.savefig(output, dpi=160)
    plt.close(fig)
    print(f"Saved runtime plot: {output}")
    return output


def plot_coordinates(
    method: str,
    n_samples: int,
    results_dir: Path = config.SMALL_RESULTS_DIR,
    output: Path | None = None,
    max_points: int = config.SMALL_MAX_PLOT_POINTS,
    seed: int = 42,
    color_by: str = "rating",
    min_cluster_size: int = config.SMALL_MIN_CLUSTER_SIZE,
) -> Path:
    results_dir = Path(results_dir)
    coordinates_path = results_dir / "coordinates" / f"coords_{method}_{n_samples}.csv"
    if not coordinates_path.exists():
        raise FileNotFoundError(f"Missing coordinates file: {coordinates_path}")

    coords = pd.read_csv(coordinates_path)
    if len(coords) > max_points:
        coords = coords.sample(max_points, random_state=seed)

    label = config.METHOD_LABELS.get(method, method)
    fig, ax = plt.subplots(figsize=(8, 6))

    if color_by == "cluster":
        try:
            import hdbscan
        except ImportError as exc:
            raise RuntimeError("Install hdbscan to create cluster-colored plots.") from exc

        clusterer = hdbscan.HDBSCAN(min_cluster_size=min_cluster_size)
        labels = clusterer.fit_predict(coords[["x", "y"]])
        scatter = ax.scatter(
            coords["x"],
            coords["y"],
            c=labels,
            cmap="tab20",
            s=8,
            alpha=0.7,
            linewidths=0,
        )
        fig.colorbar(scatter, ax=ax, label="Cluster (-1 = noise)")
    elif color_by == "rating" and "rating" in coords.columns and coords["rating"].notna().any():
        scatter = ax.scatter(
            coords["x"],
            coords["y"],
            c=coords["rating"],
            cmap="viridis",
            s=8,
            alpha=0.65,
            linewidths=0,
        )
        fig.colorbar(scatter, ax=ax, label="Rating")
    else:
        ax.scatter(coords["x"], coords["y"], s=8, alpha=0.65, linewidths=0)

    ax.set_title(f"{label} projection of review embeddings")
    ax.set_xlabel("Component 1")
    ax.set_ylabel("Component 2")
    ax.grid(True, alpha=0.2)

    if output is None:
        suffix = "_clusters" if color_by == "cluster" else ""
        output = (
            results_dir
            / "plots"
            / "embeddings"
            / f"embedding_{method}_{n_samples}{suffix}.png"
        )
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)

    fig.tight_layout()
    fig.savefig(output, dpi=180)
    plt.close(fig)
    print(f"Saved coordinates plot: {output}")
    return output
