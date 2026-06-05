from __future__ import annotations

from pathlib import Path
from typing import Sequence

import config
from src.dim_reduction import run_benchmark
from src.embeddings import prepare_embeddings


def _as_list(values: Sequence[str] | Sequence[int]) -> list:
    return list(values)


def run_local_dim_reduction_flow(
    n_values: Sequence[int] = config.SMALL_N_VALUES,
    methods: Sequence[str] = config.SMALL_METHODS,
    results_dir: Path = config.SMALL_RESULTS_DIR,
    model_name: str = config.MODEL_NAME,
    batch_size: int = config.SMALL_BATCH_SIZE,
    device: str | None = None,
    timing_mode: str = config.SMALL_TIMING_MODE,
    repeats: int = config.SMALL_REPEATS,
    warmup_samples: int = config.SMALL_WARMUP_SAMPLES,
    random_state: str | int | None = config.SMALL_RANDOM_STATE,
    max_plot_points: int = config.SMALL_MAX_PLOT_POINTS,
    cluster_methods: Sequence[str] = config.SMALL_CLUSTER_METHODS,
    force: bool = False,
) -> Path:
    """Run the complete local small-data dimensionality-reduction workflow."""
    n_values = sorted(int(value) for value in _as_list(n_values))
    methods = [str(method).lower() for method in _as_list(methods)]
    cluster_methods = [str(method).lower() for method in _as_list(cluster_methods)]
    results_dir = Path(results_dir)
    data_dir = results_dir / "data"
    plots_dir = results_dir / "plots"

    unknown_methods = sorted(set(methods) - set(config.METHODS))
    if unknown_methods:
        raise ValueError(f"Unknown methods: {unknown_methods}. Valid methods: {config.METHODS}")
    if not n_values:
        raise ValueError("n_values cannot be empty")

    max_samples = max(n_values)
    print("=== Local small dimensionality-reduction flow ===")
    print(f"Results dir: {results_dir}")
    print(f"Data dir: {data_dir}")
    print(f"Methods: {methods}")
    print(f"Sample sizes: {n_values}")

    prepare_embeddings(
        n_samples=max_samples,
        output_dir=data_dir,
        model_name=model_name,
        batch_size=batch_size,
        device=device,
        force=force,
    )

    for n_samples in n_values:
        for method in methods:
            benchmark_path = results_dir / "benchmarks" / f"benchmark_{method}_{n_samples}.csv"
            coordinates_path = results_dir / "coordinates" / f"coords_{method}_{n_samples}.csv"

            if benchmark_path.exists() and coordinates_path.exists() and not force:
                print(f"Reusing benchmark and coordinates: {method}, n={n_samples}")
                continue

            run_benchmark(
                method=method,
                n_samples=n_samples,
                data_dir=data_dir,
                results_dir=results_dir,
                max_samples=max_samples,
                timing_mode=timing_mode,
                repeats=repeats,
                warmup_samples=warmup_samples,
                random_state=random_state,
            )

    from src.dim_reduction_plots import merge_benchmark_results, plot_coordinates, plot_runtime

    results = merge_benchmark_results(results_dir)
    plot_runtime(results, plots_dir / "time_by_method.png", yscale="linear", methods=methods)
    plot_runtime(results, plots_dir / "time_by_method_log.png", yscale="log", methods=methods)

    for n_samples in n_values:
        for method in methods:
            plot_coordinates(
                method=method,
                n_samples=n_samples,
                results_dir=results_dir,
                output=plots_dir / "embeddings" / f"embedding_{method}_{n_samples}.png",
                max_points=max_plot_points,
                color_by="rating",
            )

    for method in cluster_methods:
        if method not in methods:
            continue
        plot_coordinates(
            method=method,
            n_samples=max_samples,
            results_dir=results_dir,
            output=plots_dir / "embeddings" / f"embedding_{method}_{max_samples}_clusters.png",
            max_points=max_plot_points,
            color_by="cluster",
        )

    print("=== Local flow finished ===")
    print(f"Results: {results_dir}")
    print(f"Merged benchmark: {results_dir / 'benchmarks' / 'results_all.csv'}")
    print(f"Runtime plots: {plots_dir}")
    print(f"Embedding plots: {plots_dir / 'embeddings'}")
    return results_dir
