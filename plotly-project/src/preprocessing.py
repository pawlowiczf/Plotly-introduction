import pandas as pd

def clean(df: pd.DataFrame) -> pd.DataFrame:
    df = df.drop(columns=["images"])
    df = df.dropna(subset=["text", "rating"])
    df = df[df["text"].str.strip() != ""]
    df = df.reset_index(drop=True)
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df["text_len"] = df["text"].str.len()
    df["title_len"] = df["title"].str.len()
    return df
