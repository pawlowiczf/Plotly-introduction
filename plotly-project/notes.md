### Analiza opinii klientów i segmentacja produktów
Celem projektu jest analiza dużego zbioru recenzji produktów oraz segmentacja produktów lub opinii na podstawie ocen i treści tekstowych.

Należy przygotować reprezentację recenzji lub produktów i zbadać, jakie grupy opinii występują w danych.

Wymagania:
przygotowanie danych recenzji,
preprocessing tekstu,
analiza ocen i kategorii produktów,
przygotowanie embeddingów tekstowych lub cech produktów,
wizualizacja klastrów opinii,
interpretacja segmentów produktów lub klientów.

Element związany z redukcją wymiaru:
Należy porównać co najmniej dwie metody spośród: PCA, UMAP, PaCMAP, FIt-SNE/flt-SNE.

Element rozszerzony:
Można dodać analizę sentymentu albo porównanie kategorii produktów.

Przykładowe dane i narzędzia:
Amazon Reviews Dataset, Python NLP, Orange, Dash, Tableau.

`pip install datasets pandas numpy tqdm nltk scikit-learn sentence-transformers umap-learn pacmap openTSNE hdbscan plotly matplotlib seaborn vaderSentiment`