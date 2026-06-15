# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

A university (UMISI) data-analysis project on the **Amazon Reviews 2023 — Electronics** dataset. Two goals: (1) exploratory analysis / EDA of reviews + product metadata, and (2) benchmarking and visualizing four dimensionality-reduction methods (PCA, UMAP, PaCMAP, FIt-SNE via openTSNE) on sentence embeddings of review text. Project notes/README are in Polish; code and identifiers are in English.

## Environment & commands

All commands assume the repo root `plotly-project/` and a virtualenv at `.venv/`.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

`requirements.txt` pins a CPU-only stack (`torch==2.5.1+cpu` via the PyTorch CPU extra-index-url, `sentence-transformers==3.3.1`, `transformers==4.46.3`, `datasets<4.0.0`). Keep these pins — newer `datasets` and the transformers/sentence-transformers combo break the loading paths.

Run the local dimensionality-reduction benchmark (downloads data + embeds on first run, then reuses cached artifacts):

```powershell
python .\scripts\run_small_dim_reduction.py --n-values 500,1000,2000,5000 --methods pca,umap,pacmap,fitsne --repeats 2 --warmup-samples 250
```

Add `--force` to recompute embeddings/reductions/plots; `--random-state none` to trade determinism for UMAP parallelism. Defaults for every flag live in `config.py` (the `SMALL_*` constants).

Find stray points in a 2D projection (writes `<input>_<suffix>.csv` next to the input):

```powershell
python .\scripts\find_outliers.py dim_reduction\results\coordinates\coords_pacmap_50000.csv --method tips --top 50
```

Notebooks are run interactively (`notebooks/01_loading.ipynb` then `02_eda.ipynb`). There is no test suite, linter config, or build step — `.ruff-cache/` in `.gitignore` implies ruff is used ad hoc but no config is committed.

## Architecture

There are **two independent pipelines** that share `config.py` but otherwise do not talk to each other. They even have *separate* loading and data-handling code — do not assume a change in one affects the other.

### 1. Notebook / EDA pipeline

`notebooks/*.ipynb` → `src/loader.py`, `src/preprocessing.py`, `src/analysis.py`, `src/plots.py`, `src/storage.py`.

- Notebooks add `sys.path.append("..")` then `import config` and `from src import ...`.
- `src/storage.py` caches each stage as Parquet under `data/` (gitignored). `storage.cached(name, build_fn)` returns the cached stage or builds+persists it; `save_stage`/`load_stage` move DataFrames between the two notebooks. `01_loading` produces `reviews_clean` and `meta_clean`; `02_eda` consumes them.
- `src/loader.py` loads via streaming and materializes with `list(ds.take(n))`. **Meta is read as raw Parquet on purpose** (`hf://datasets/.../*.parquet`) because the dataset's loading script forces a schema that fails to cast nested fields like `images` (`ArrowNotImplementedError`).
- `src/plots.py` returns Plotly figures (interactive, the project's focus) with `*_mpl` matplotlib twins for a few of them. Review-level plots take the merged reviews DataFrame; `category_treemap`/`price_vs_rating` operate on product-level metadata.

### 2. Dimensionality-reduction benchmark pipeline

`scripts/run_small_dim_reduction.py` (thin CLI) → `src/local_pipeline.py` (orchestrator) → `src/embeddings.py` + `src/dim_reduction.py` + `src/dim_reduction_plots.py`.

Flow inside `run_local_dim_reduction_flow`:
1. `embeddings.prepare_embeddings(max(n_values))` — streams reviews from HF, normalizes text (`src/text.py`), encodes with SentenceTransformer (`all-MiniLM-L6-v2`), saves `reviews_<n>.csv` + `embeddings_<n>.npy`. Smaller `n` reuse the largest embeddings array sliced to size (see `load_embeddings`/`load_review_info` fallback logic).
2. For each `(n_samples, method)`: `dim_reduction.run_benchmark` builds the reducer (`make_reducer`), optionally warms up, runs `repeats` timed fits, and writes `benchmark_<method>_<n>.csv`, `timings_<method>_<n>.csv`, and `coords_<method>_<n>.csv`. Existing benchmark+coords pairs are skipped unless `--force`.
3. `dim_reduction_plots.merge_benchmark_results` concatenates all `benchmark_*.csv` into `results_all.csv`, then `plot_runtime` (linear + log) and `plot_coordinates` produce PNGs. Cluster plots re-color the largest sample via HDBSCAN.

Method-specific gotchas in `src/dim_reduction.py`:
- FIt-SNE uses openTSNE's `reducer.fit(...)` (returns an array); every other method uses `fit_transform`.
- `random_state` is parsed by `parse_random_state` — the string `"none"`/`"null"` → `None`, which for UMAP switches to multi-threaded mode (`n_jobs=available_threads()`).
- `available_threads()` reads `SLURM_CPUS_PER_TASK` / `CPU_THREADS` env vars (defaults to 1). The committed `dim_reduction/results/` (n up to 50000) was produced on a SLURM cluster; the local flow is the laptop-sized version of the same code.

## Results directories (mind what is committed)

- `dim_reduction/results/` — **committed, treat as read-only.** Precomputed large-scale benchmark/coordinates/plots (n = 5000–50000). Regenerating these is not the local workflow.
- `dim_reduction/results_small/` — **gitignored.** Everything `run_small_dim_reduction.py` writes locally (`data/`, `benchmarks/`, `coordinates/`, `plots/`).
- `data/` — **gitignored.** Parquet stage cache for the notebooks.

Both pipelines key all output filenames on `<method>` and `<n_samples>`, and `config.py` is the single source of truth for dataset names, the model, the method list/labels, paths, and the `SMALL_*` defaults — change defaults there rather than hardcoding in scripts.
