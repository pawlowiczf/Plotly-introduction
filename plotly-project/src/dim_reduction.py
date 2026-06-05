from __future__ import annotations

import os
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

import config


@dataclass(frozen=True)
class BenchmarkArtifacts:
    benchmark_path: Path
    timings_path: Path
    coordinates_path: Path
    times: list[float]


def parse_random_state(value: str | int | None) -> int | None:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    if value.lower() in {"none", "null"}:
        return None
    return int(value)


def available_threads() -> int:
    return int(os.environ.get("SLURM_CPUS_PER_TASK") or os.environ.get("CPU_THREADS") or "1")


def load_embeddings(data_dir: Path, n_samples: int, max_samples: int | None = None) -> np.ndarray:
    data_dir = Path(data_dir)
    exact_path = data_dir / f"embeddings_{n_samples}.npy"
    fallback_n = max_samples or config.SMALL_MAX_SAMPLES
    fallback_path = data_dir / f"embeddings_{fallback_n}.npy"

    if exact_path.exists():
        embeddings = np.load(exact_path)
    elif fallback_path.exists():
        embeddings = np.load(fallback_path)[:n_samples]
    else:
        raise FileNotFoundError(
            "Missing embeddings. Run scripts/run_small_dim_reduction.py first, "
            f"or prepare {exact_path}."
        )

    if len(embeddings) < n_samples:
        raise ValueError(f"Only {len(embeddings)} embeddings available, expected {n_samples}")

    return embeddings[:n_samples].astype(np.float32, copy=False)


def load_review_info(data_dir: Path, n_samples: int, max_samples: int | None = None) -> pd.DataFrame:
    data_dir = Path(data_dir)
    exact_path = data_dir / f"reviews_{n_samples}.csv"
    fallback_n = max_samples or config.SMALL_MAX_SAMPLES
    fallback_path = data_dir / f"reviews_{fallback_n}.csv"

    if exact_path.exists():
        reviews = pd.read_csv(exact_path)
    elif fallback_path.exists():
        reviews = pd.read_csv(fallback_path).head(n_samples)
    else:
        reviews = pd.DataFrame(index=range(n_samples))

    return reviews.head(n_samples).reset_index(drop=True)


def make_reducer(method: str, random_state: int | None):
    if method == "pca":
        from sklearn.decomposition import PCA

        return PCA(n_components=2, random_state=random_state)

    if method == "umap":
        import umap

        if random_state is None:
            return umap.UMAP(n_components=2, n_jobs=available_threads())
        return umap.UMAP(n_components=2, random_state=random_state)

    if method == "pacmap":
        import pacmap

        return pacmap.PaCMAP(n_components=2, random_state=random_state)

    if method == "fitsne":
        from openTSNE import TSNE

        return TSNE(
            n_components=2,
            perplexity=30,
            n_iter=500,
            initialization="pca",
            negative_gradient_method="fft",
            n_jobs=available_threads(),
            random_state=random_state,
        )

    raise ValueError(f"Unknown method: {method}")


def fit_reducer(method: str, reducer, embeddings: np.ndarray) -> np.ndarray:
    if method == "fitsne":
        return np.asarray(reducer.fit(embeddings))
    return reducer.fit_transform(embeddings)


def run_warmup(
    method: str,
    embeddings: np.ndarray,
    warmup_samples: int,
    random_state: int | None,
) -> None:
    if warmup_samples <= 0:
        return

    sample_size = min(warmup_samples, len(embeddings))
    print(f"Warm-up {method}: n_samples={sample_size}, dim={embeddings.shape[1]}")
    reducer = make_reducer(method, random_state)
    fit_reducer(method, reducer, embeddings[:sample_size])


def run_timed_repeats(
    method: str,
    embeddings: np.ndarray,
    timing_mode: str,
    repeats: int,
    warmup_samples: int,
    random_state: int | None,
) -> tuple[np.ndarray, list[float]]:
    if timing_mode not in {"end-to-end", "fit-only"}:
        raise ValueError("timing_mode must be 'end-to-end' or 'fit-only'")

    if timing_mode == "fit-only":
        run_warmup(method, embeddings, warmup_samples, random_state)

    coordinates = None
    times: list[float] = []

    for repeat in range(1, repeats + 1):
        if timing_mode == "fit-only":
            reducer = make_reducer(method, random_state)
            start = time.perf_counter()
            coordinates = fit_reducer(method, reducer, embeddings)
        else:
            start = time.perf_counter()
            reducer = make_reducer(method, random_state)
            coordinates = fit_reducer(method, reducer, embeddings)

        elapsed = time.perf_counter() - start
        times.append(elapsed)
        print(f"Repeat {repeat}/{repeats}: {elapsed:.4f}s")

    if coordinates is None:
        raise RuntimeError("No coordinates were produced")

    return coordinates, times


def save_coordinates(
    method: str,
    n_samples: int,
    coordinates: np.ndarray,
    data_dir: Path,
    coordinates_dir: Path,
    max_samples: int | None = None,
) -> Path:
    reviews = load_review_info(data_dir, n_samples, max_samples=max_samples)
    coordinates_dir = Path(coordinates_dir)
    coordinates_dir.mkdir(parents=True, exist_ok=True)

    coords = pd.DataFrame(
        {
            "method": method,
            "n_samples": n_samples,
            "point_id": np.arange(len(coordinates)),
            "x": coordinates[:, 0],
            "y": coordinates[:, 1],
        }
    )

    for col in ["rating", "parent_asin"]:
        if col in reviews.columns:
            coords[col] = reviews[col].values

    output_path = coordinates_dir / f"coords_{method}_{n_samples}.csv"
    coords.to_csv(output_path, index=False)
    return output_path


def run_benchmark(
    method: str,
    n_samples: int,
    data_dir: Path = config.SMALL_DATA_DIR,
    results_dir: Path = config.SMALL_RESULTS_DIR,
    max_samples: int | None = config.SMALL_MAX_SAMPLES,
    timing_mode: str = config.SMALL_TIMING_MODE,
    repeats: int = config.SMALL_REPEATS,
    warmup_samples: int = config.SMALL_WARMUP_SAMPLES,
    random_state: str | int | None = config.SMALL_RANDOM_STATE,
) -> BenchmarkArtifacts:
    data_dir = Path(data_dir)
    results_dir = Path(results_dir)
    benchmarks_dir = results_dir / "benchmarks"
    coordinates_dir = results_dir / "coordinates"
    benchmarks_dir.mkdir(parents=True, exist_ok=True)
    coordinates_dir.mkdir(parents=True, exist_ok=True)

    parsed_random_state = parse_random_state(random_state)
    embeddings = load_embeddings(data_dir, n_samples, max_samples=max_samples)

    print(
        f"Running {method}: n_samples={n_samples}, dim={embeddings.shape[1]}, "
        f"timing_mode={timing_mode}, repeats={repeats}, "
        f"warmup_samples={warmup_samples}, random_state={random_state}"
    )

    coordinates, times = run_timed_repeats(
        method,
        embeddings,
        timing_mode,
        repeats,
        warmup_samples,
        parsed_random_state,
    )

    median_time = float(np.median(times))
    row = {
        "method": method,
        "n_samples": n_samples,
        "time_seconds": round(median_time, 4),
        "time_seconds_mean": round(float(np.mean(times)), 4),
        "time_seconds_std": round(float(np.std(times, ddof=1)) if len(times) > 1 else 0.0, 4),
        "time_seconds_min": round(float(np.min(times)), 4),
        "time_seconds_max": round(float(np.max(times)), 4),
        "repeats": repeats,
        "timing_mode": timing_mode,
        "warmup_samples": warmup_samples,
        "random_state": str(random_state),
    }

    benchmark_path = benchmarks_dir / f"benchmark_{method}_{n_samples}.csv"
    pd.DataFrame([row]).to_csv(benchmark_path, index=False)

    timings_path = benchmarks_dir / f"timings_{method}_{n_samples}.csv"
    pd.DataFrame(
        [
            {
                "method": method,
                "n_samples": n_samples,
                "repeat": repeat,
                "time_seconds": round(value, 4),
                "timing_mode": timing_mode,
                "warmup_samples": warmup_samples,
                "random_state": str(random_state),
            }
            for repeat, value in enumerate(times, start=1)
        ]
    ).to_csv(timings_path, index=False)

    coordinates_path = save_coordinates(
        method,
        n_samples,
        coordinates,
        data_dir,
        coordinates_dir,
        max_samples=max_samples,
    )

    print(f"Saved benchmark: {benchmark_path}")
    print(f"Saved repeat timings: {timings_path}")
    print(f"Saved coordinates: {coordinates_path}")

    return BenchmarkArtifacts(benchmark_path, timings_path, coordinates_path, times)
