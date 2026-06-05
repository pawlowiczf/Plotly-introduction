from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import config


def parse_int_list(value: str) -> list[int]:
    return [int(item.strip()) for item in value.split(",") if item.strip()]


def parse_str_list(value: str) -> list[str]:
    return [item.strip().lower() for item in value.split(",") if item.strip()]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the local small-data dimensionality-reduction flow."
    )
    parser.add_argument(
        "--n-values",
        default=",".join(str(value) for value in config.SMALL_N_VALUES),
        help="Comma-separated sample sizes, for example 200,500,1000.",
    )
    parser.add_argument(
        "--methods",
        default=",".join(config.SMALL_METHODS),
        help="Comma-separated methods: pca,umap,pacmap,fitsne.",
    )
    parser.add_argument("--results-dir", type=Path, default=config.SMALL_RESULTS_DIR)
    parser.add_argument("--model", default=config.MODEL_NAME)
    parser.add_argument("--batch-size", type=int, default=config.SMALL_BATCH_SIZE)
    parser.add_argument("--device", default=None, help="Optional device, for example cpu or cuda.")
    parser.add_argument(
        "--timing-mode",
        choices=["end-to-end", "fit-only"],
        default=config.SMALL_TIMING_MODE,
    )
    parser.add_argument("--repeats", type=int, default=config.SMALL_REPEATS)
    parser.add_argument("--warmup-samples", type=int, default=config.SMALL_WARMUP_SAMPLES)
    parser.add_argument(
        "--random-state",
        default=config.SMALL_RANDOM_STATE,
        help="Integer seed or 'none'. Local default is deterministic.",
    )
    parser.add_argument("--max-plot-points", type=int, default=config.SMALL_MAX_PLOT_POINTS)
    parser.add_argument(
        "--cluster-methods",
        default=",".join(config.SMALL_CLUSTER_METHODS),
        help="Comma-separated methods for extra HDBSCAN cluster plots. Empty disables them.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Recompute embeddings, reductions and plots even if files already exist.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    from src.local_pipeline import run_local_dim_reduction_flow

    run_local_dim_reduction_flow(
        n_values=parse_int_list(args.n_values),
        methods=parse_str_list(args.methods),
        results_dir=args.results_dir,
        model_name=args.model,
        batch_size=args.batch_size,
        device=args.device,
        timing_mode=args.timing_mode,
        repeats=args.repeats,
        warmup_samples=args.warmup_samples,
        random_state=args.random_state,
        max_plot_points=args.max_plot_points,
        cluster_methods=parse_str_list(args.cluster_methods),
        force=args.force,
    )


if __name__ == "__main__":
    main()
