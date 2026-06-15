"""Find outliers in a 2D dimensionality-reduction coordinates CSV.

Reads a coords_<method>_<n>.csv file (columns: x, y, point_id, rating,
parent_asin, ...) and flags points that stand apart in the projection.
Two scoring methods are available:

* ``isolation`` (default) -- distance to the k-th nearest neighbour. This
  finds genuinely lonely points sitting in empty space (the stray dots you
  can circle by eye), not whole low-density bands. Recommended.
* ``radial`` -- distance from a robust (median) center. Flags everything
  far from the bulk, including dense arms/bands that merely sit off-center.

Both are turned into a modified z-score via the median absolute deviation
(MAD) so the threshold is insensitive to the very outliers we look for.

Usage:
    python scripts/find_outliers.py \
        dim_reduction/results/coordinates/coords_pacmap_50000.csv \
        --method isolation --z 4 --top 50

Output:
    - prints the outliers sorted by score (most isolated / farthest first)
    - writes <input_stem>_outliers.csv next to the input file
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree


def _robust_z(values: np.ndarray) -> np.ndarray:
    """Modified z-score using the median absolute deviation (MAD)."""
    med = np.median(values)
    mad = np.median(np.abs(values - med))
    scale = 1.4826 * mad if mad > 0 else values.std()
    if scale <= 0:
        return np.zeros_like(values)
    return (values - med) / scale


def find_tips(df: pd.DataFrame, top: int = 25, min_sep: float = 2.0) -> pd.DataFrame:
    """Return the distinct extreme tips of the projection.

    Points are ranked by distance from the median center, then selected
    greedily so each kept point sits at least ``min_sep`` away from all
    previously kept ones. This yields one representative per isolated
    streak/tip instead of a pile-up at the single farthest spot -- i.e. the
    handful of stray points you would circle by eye.
    """
    xy = df[["x", "y"]].to_numpy()
    center = np.median(xy, axis=0)
    score = np.hypot(xy[:, 0] - center[0], xy[:, 1] - center[1])

    ordered = np.argsort(score)[::-1]
    kept_pos: list[np.ndarray] = []
    kept_rows: list[int] = []
    for i in ordered:
        p = xy[i]
        if all(np.hypot(*(p - q)) >= min_sep for q in kept_pos):
            kept_pos.append(p)
            kept_rows.append(i)
        if len(kept_rows) >= top:
            break

    out = df.iloc[kept_rows].copy()
    out["score"] = score[kept_rows]
    out = out.sort_values("score", ascending=False)
    out.insert(0, "label", range(1, len(out) + 1))
    return out


def find_outliers(
    df: pd.DataFrame, method: str = "isolation", z_thresh: float = 4.0, k: int = 10
) -> pd.DataFrame:
    """Return rows flagged as outliers under the chosen scoring method."""
    xy = df[["x", "y"]].to_numpy()

    if method == "isolation":
        # Distance to the k-th nearest neighbour: large => isolated point.
        tree = cKDTree(xy)
        # k+1 because the first neighbour is the point itself (distance 0).
        dists, _ = tree.query(xy, k=k + 1)
        score_raw = dists[:, -1]
    elif method == "radial":
        center = np.median(xy, axis=0)
        score_raw = np.hypot(xy[:, 0] - center[0], xy[:, 1] - center[1])
    else:
        raise ValueError(f"Unknown method: {method!r}")

    out = df.copy()
    out["score"] = score_raw
    out["robust_z"] = _robust_z(score_raw)
    out = out[out["robust_z"] >= z_thresh]
    return out.sort_values("score", ascending=False)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", type=Path, help="Path to coords_<method>_<n>.csv")
    parser.add_argument(
        "--method", choices=["tips", "isolation", "radial"], default="tips",
        help="Scoring method (default: tips -- distinct extreme stray points).",
    )
    parser.add_argument(
        "--z", type=float, default=4.0,
        help="Modified z-score threshold for isolation/radial (default: 4.0).",
    )
    parser.add_argument(
        "--k", type=int, default=10,
        help="k for k-NN distance in isolation mode (default: 10).",
    )
    parser.add_argument(
        "--min-sep", type=float, default=2.0,
        help="Min 2D separation between kept tips in tips mode (default: 2.0).",
    )
    parser.add_argument(
        "--top", type=int, default=25,
        help="How many outliers to keep/print (default: 25).",
    )
    args = parser.parse_args()

    df = pd.read_csv(args.csv)

    if args.method == "tips":
        outliers = find_tips(df, top=args.top, min_sep=args.min_sep)
        suffix = "tips"
    else:
        outliers = find_outliers(df, method=args.method, z_thresh=args.z, k=args.k)
        suffix = "outliers"

    cols = [c for c in ["label", "point_id", "robust_z", "score", "x", "y", "rating", "parent_asin"]
            if c in outliers.columns]
    outliers = outliers[cols]

    print(f"Loaded {len(df)} points from {args.csv}")
    if args.method == "tips":
        print(f"Method: tips (top={args.top}, min_sep={args.min_sep})")
    else:
        print(f"Method: {args.method} (z >= {args.z}"
              + (f", k={args.k}" if args.method == "isolation" else "") + ")")
    print(f"Outliers: {len(outliers)}")
    print(f"Unique parent_asin among outliers: {outliers['parent_asin'].nunique()}")
    print()
    with pd.option_context("display.max_rows", None, "display.width", 160):
        print(outliers.head(args.top).to_string(index=False))

    out_path = args.csv.with_name(f"{args.csv.stem}_{suffix}.csv")
    outliers.to_csv(out_path, index=False)
    print(f"\nSaved {len(outliers)} {suffix} -> {out_path}")


if __name__ == "__main__":
    main()
