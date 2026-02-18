import pandas as pd
from src.storage import load_patents

def search_by_keyword(keyword: str) -> pd.DataFrame:
    df = load_patents()
    if df.empty:
        print("No patents in database yet. Run a fetch first.")
        return df

    keyword_lower = keyword.lower()
    # Search title only (abstract not available from this API endpoint)
    mask = df["title"].str.lower().str.contains(keyword_lower, na=False)

    results = df[mask].copy()
    print(f"Found {len(results)} patents matching '{keyword}'")
    return results


def count_by_month(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate patent counts by month.
    
    Args:
        df: DataFrame of patents (must have a 'date' column)
    
    Returns:
        DataFrame with columns: month, count
    """
    if df.empty:
        return df

    df["date"] = pd.to_datetime(df["date"])
    df["month"] = df["date"].dt.to_period("M")
    monthly = df.groupby("month").size().reset_index(name="count")
    monthly["month"] = monthly["month"].astype(str)
    return monthly


def compare_keywords(keywords: list[str]) -> pd.DataFrame:
    """
    Compare monthly patent counts across multiple keywords.

    Args:
        keywords: List of search terms to compare

    Returns:
        DataFrame with a column per keyword showing monthly counts
    """
    df = load_patents()

    if df.empty:
        print("No patents in database yet. Run a fetch first.")
        return pd.DataFrame()

    combined = None

    for keyword in keywords:
        keyword_lower = keyword.lower()
        mask = df["title"].str.lower().str.contains(keyword_lower, na=False)
        filtered = df[mask].copy()
        monthly = count_by_month(filtered)

        if monthly.empty:
            print(f"No results found for keyword: '{keyword}', skipping.")
            continue

        monthly = monthly.rename(columns={"count": keyword})

        if combined is None:
            combined = monthly
        else:
            combined = pd.merge(combined, monthly, on="month", how="outer")

    if combined is not None:
        combined = combined.sort_values("month").fillna(0)
    else:
        combined = pd.DataFrame()

    return combined