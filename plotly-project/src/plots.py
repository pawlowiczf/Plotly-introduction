import pandas as pd
import plotly.express as px
from plotly.graph_objects import Figure


def rating_histogram(df: pd.DataFrame) -> Figure:
    return px.histogram(df, x="rating", nbins=5, title="Rating distribution")


def text_length_histogram(df: pd.DataFrame) -> Figure:
    return px.histogram(df, x="text_len", title="Review length distribution")


def reviews_over_time(df: pd.DataFrame) -> Figure:
    counts = df.groupby(df["timestamp"].dt.year).size().reset_index(name="count")
    counts.columns = ["year", "count"]
    return px.bar(counts, x="year", y="count", title="Reviews over time")
