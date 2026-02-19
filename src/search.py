import pandas as pd
from src.storage import load_patents, load_publications


def search_by_keyword(keyword: str, source: str = "patents") -> pd.DataFrame:
    """
    Search for a keyword in titles and abstracts.

    Args:
        keyword: Term to search for (case-insensitive)
        source: 'patents', 'arxiv', 'semantic_scholar', or 'publications' (all pubs)

    Returns:
        Filtered DataFrame of matching records
    """
    if source == "patents":
        df = load_patents()
        title_col = "title"
        abstract_col = "abstract"
    elif source in ("arxiv", "semantic_scholar"):
        df = load_publications(source=source)
        title_col = "title"
        abstract_col = "abstract"
    else:
        df = load_publications()
        title_col = "title"
        abstract_col = "abstract"

    if df.empty:
        return df

    keyword_lower = keyword.lower()
    mask = (
        df[title_col].str.lower().str.contains(keyword_lower, na=False) |
        df[abstract_col].str.lower().str.contains(keyword_lower, na=False)
    )

    return df[mask].copy()


def count_by_month(df: pd.DataFrame, date_col: str = "date") -> pd.DataFrame:
    """
    Aggregate record counts by month.

    Args:
        df: DataFrame with a date column
        date_col: Name of the date column

    Returns:
        DataFrame with columns: month, count
    """
    if df.empty:
        return pd.DataFrame(columns=["month", "count"])

    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df = df.dropna(subset=[date_col])
    df["month"] = df[date_col].dt.to_period("M")
    monthly = df.groupby("month").size().reset_index(name="count")
    monthly["month"] = monthly["month"].astype(str)
    return monthly


def compare_keywords(keywords: list[str], source: str = "patents") -> pd.DataFrame:
    """
    Compare monthly counts across multiple keywords.

    Args:
        keywords: List of search terms to compare
        source: 'patents', 'arxiv', 'semantic_scholar', or 'publications'

    Returns:
        DataFrame with a column per keyword showing monthly counts
    """
    combined = None

    for keyword in keywords:
        results = search_by_keyword(keyword, source=source)
        monthly = count_by_month(results)

        if monthly.empty:
            continue

        monthly = monthly.rename(columns={"count": keyword})

        if combined is None:
            combined = monthly
        else:
            combined = pd.merge(combined, monthly, on="month", how="outer")

    if combined is not None:
        combined = combined.sort_values("month").fillna(0)
        return combined

    return pd.DataFrame()