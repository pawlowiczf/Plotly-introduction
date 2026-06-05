# Redukcja wymiaru lokalnie

Gotowe duze wyniki eksperymentu sa w:

```text
dim_reduction/results
```

Lokalne eksperymenty zapisujemy w:

```text
dim_reduction/results_small
```

Ten katalog jest ignorowany przez Git, bo lokalne wyniki moga byc duze i latwo je
odtworzyc komenda ponizej.

## Instalacja

Komendy ponizej zakladaja, ze terminal jest w katalogu `plotly-project\dim_reduction`
czyli tam, gdzie ten README.

```bash
python -m venv ..\.venv
..\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r ..\requirements.txt
```

Jesli zaleznosci byly juz instalowane wczesniej i cos sie sypie:

```bash
python -m pip install --upgrade --force-reinstall -r ..\requirements.txt
```

## Lokalny eksperyment

Porownujemy 4 metody redukcji wymiaru na lokalnej, mniejszej probce:

```bash
python ..\scripts\run_small_dim_reduction.py --n-values 500,1000,2000,5000 --methods pca,umap,pacmap,fitsne --repeats 2 --warmup-samples 250
```

To powinno liczyc sie mniej wiecej kilka minut, zalezne od komputera.

## Efekt

Po uruchomieniu powstaje struktura:

```text
results_small/
  data/          reviews_*.csv i embeddings_*.npy
  benchmarks/    benchmark_*.csv, timings_*.csv, results_all.csv
  coordinates/   coords_<method>_<n>.csv
  plots/         wykres czasu, mapy 2D embeddingow i cluster ploty
```

Najwazniejsze pliki:

```text
dim_reduction/results_small/benchmarks/results_all.csv
dim_reduction/results_small/plots/time_by_method.png
dim_reduction/results_small/plots/time_by_method_log.png
dim_reduction/results_small/plots/embeddings/
```

Cluster ploty sa generowane dla wszystkich metod: PCA, UMAP, PaCMAP i FIt-SNE.
