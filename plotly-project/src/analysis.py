import pandas as pd


def data_quality(df: pd.DataFrame) -> None:
    print("--- Missing values ---")
    print(df.isnull().sum())
    print(f"\nEmpty strings (text): {(df['text'] == '').sum()}")
    print(f"Empty strings (title): {(df['title'] == '').sum()}")
    print(f"\nDuplicates (user_id + asin): {df.duplicated(subset=['user_id', 'asin']).sum()}")
    print(f"Duplicates (full row): {df.duplicated().sum()}")
    print(f"\nDate range: {df['timestamp'].min().date()} → {df['timestamp'].max().date()}")
    print(f"Unique products (asin): {df['asin'].nunique()}")
    print(f"Unique users: {df['user_id'].nunique()}")
    print(f"Verified purchase: {df['verified_purchase'].value_counts().to_dict()}")
    print("\n--- Rating distribution ---")
    print(df["rating"].value_counts().sort_index())
