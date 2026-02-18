from src.storage import init_db, save_patents
from src.fetch import fetch_patents
from src.search import search_by_keyword, count_by_month, compare_keywords

# ── Configuration ────────────────────────────────────────────────────────────

START_DATE = "2023-01-01"
END_DATE   = "2025-12-31"

# Keywords to fetch and store - each one runs a full date-range fetch
FETCH_KEYWORDS = [
    # Full phrases (already fetched)
    "autonomous underwater vehicle",
    "unmanned underwater vehicle",
    "unmanned surface vehicle",
    "autonomous surface vehicle",
    "AUV swarm",
    "UUV swarm",
    "USV swarm",
    "underwater swarm",
    "underwater docking",
    "autonomous underwater docking",
    "underwater mothership",
    "maritime autonomous",

    # Broader terms likely used in titles
    "underwater robot",
    "underwater drone",
    "subsea autonomous",
    "autonomous submarine",
    "unmanned submarine",
    "underwater glider",
    "autonomous glider",
    "submersible autonomous",
    "multi-robot underwater",
    "underwater vehicle swarm",
    "cooperative underwater",
    "autonomous naval",
    "unmanned maritime",
    "underwater mine",
    "autonomous mine countermeasure",
    "undersea vehicle",
    "autonomous undersea",
]

# Keywords to compare in the trend chart (subset of above, most meaningful)
COMPARE_KEYWORDS = [
    "autonomous underwater vehicle",
    "unmanned underwater vehicle",
    "underwater robot",
    "underwater drone",
    "unmanned maritime",
]

# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    # 1. Initialize the database
    init_db()

    # 2. Fetch patents for each keyword and accumulate in the database
    print("=" * 60)
    print("PATENT FETCH PHASE")
    print(f"Date range: {START_DATE} to {END_DATE}")
    print(f"Keywords to fetch: {len(FETCH_KEYWORDS)}")
    print("=" * 60)

    total_new = 0
    for keyword in FETCH_KEYWORDS:
        print(f"\n{'─' * 60}")
        patents = fetch_patents(keyword, START_DATE, END_DATE, max_results=2000)
        saved = save_patents(patents)
        total_new += len(patents)

    print(f"\n{'=' * 60}")
    print(f"FETCH COMPLETE — {total_new} records fetched across all keywords")
    print(f"(Duplicates automatically ignored by database)")
    print("=" * 60)

    # 3. Keyword comparison across the full date range
    print("\n\n--- MONTHLY TREND COMPARISON ---")
    comparison = compare_keywords(COMPARE_KEYWORDS)
    if not comparison.empty:
        print(comparison.to_string())
    else:
        print("No data found for comparison keywords.")

    # 4. Quick summary stats per keyword
    print("\n\n--- TOTAL COUNTS PER KEYWORD ---")
    from src.storage import load_patents
    df = load_patents()
    print(f"Total unique patents in database: {len(df)}")
    print(f"Date range: {df['date'].min()} to {df['date'].max()}\n")

    for keyword in COMPARE_KEYWORDS:
        results = search_by_keyword(keyword)
        count = len(results)
        print(f"  {keyword:<40} {count:>5} patents")


if __name__ == "__main__":
    main()