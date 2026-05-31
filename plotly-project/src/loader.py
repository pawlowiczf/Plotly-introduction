import pandas as pd
from datasets import load_dataset


def load_reviews(dataset_name: str, subset: str, n: int | None = None) -> pd.DataFrame:
    ds = load_dataset(dataset_name, subset, streaming=True, trust_remote_code=True)
    records = list(ds["full"].take(n)) if n else list(ds["full"])
    return pd.DataFrame(records)
