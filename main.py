from src.storage import init_db, save_patents, save_publications, load_patents, load_publications
from src.fetch import fetch_patents
from src.fetch_publications import fetch_publications
from src.search import search_by_keyword, compare_keywords

# ── Configuration ────────────────────────────────────────────────────────────

START_DATE = "2023-01-01"
END_DATE   = "2023-12-31"

# Shortened list for testing
FETCH_KEYWORDS = [
    "autonomous underwater vehicle",
    "unmanned underwater vehicle",
    "unmanned surface vehicle",
    "autonomous surface vehicle",
]

# FETCH_KEYWORDS = [
#     "autonomous underwater vehicle",
#     "unmanned underwater vehicle",
#     "unmanned surface vehicle",
#     "autonomous surface vehicle",
#     "underwater swarm",
#     "underwater docking",
#     "underwater mothership",
#     "maritime autonomous",
#     "underwater robot",
#     "underwater drone",
#     "subsea autonomous",
#     "autonomous submarine",
#     "unmanned submarine",
#     "underwater glider",
#     "multi-robot underwater",
#     "cooperative underwater",
#     "autonomous naval",
#     "unmanned maritime",
#     "autonomous undersea",
# ]

COMPARE_KEYWORDS = [
    "autonomous underwater vehicle",
    "unmanned underwater vehicle",
    "underwater robot",
    "underwater drone",
    "unmanned maritime",
]

# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    init_db()

    # ── Patent Fetch ──────────────────────────────────────────────────────────
    print("=" * 60)
    print("PHASE 1: PATENT FETCH")
    print(f"Date range: {START_DATE} to {END_DATE}")
    print("=" * 60)

    for keyword in FETCH_KEYWORDS:
        print(f"\n{'─' * 60}")
        patents = fetch_patents(keyword, START_DATE, END_DATE, max_results=2000)
        save_patents(patents)

    patent_df = load_patents()
    print(f"\nTotal unique patents in database: {len(patent_df)}")

    # ── Publication Fetch ─────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("PHASE 2: PUBLICATION FETCH (arXiv + Semantic Scholar)")
    print(f"Date range: {START_DATE} to {END_DATE}")
    print("=" * 60)

    for keyword in FETCH_KEYWORDS:
        print(f"\n{'─' * 60}")
        print(f"Keyword: '{keyword}'")
        pubs = fetch_publications(keyword, START_DATE, END_DATE, max_results=500)
        save_publications(pubs)

    pub_df = load_publications()
    print(f"\nTotal unique publications in database: {len(pub_df)}")

    arxiv_df = load_publications(source="arxiv")
    ss_df = load_publications(source="semantic_scholar")
    print(f"  arXiv:            {len(arxiv_df)}")
    print(f"  Semantic Scholar: {len(ss_df)}")

    # ── Summary ───────────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("SUMMARY — PATENT vs PUBLICATION COUNTS PER KEYWORD")
    print("=" * 60)
    print(f"{'Keyword':<42} {'Patents':>8} {'arXiv':>8} {'SS':>8}")
    print("─" * 68)

    for keyword in COMPARE_KEYWORDS:
        p_results = search_by_keyword(keyword, source="patents")
        a_results = search_by_keyword(keyword, source="arxiv")
        s_results = search_by_keyword(keyword, source="semantic_scholar")
        print(f"  {keyword:<40} {len(p_results):>8} {len(a_results):>8} {len(s_results):>8}")

    # ── Trend Comparison ──────────────────────────────────────────────────────
    print("\n\n--- PATENT MONTHLY TRENDS ---")
    patent_comparison = compare_keywords(COMPARE_KEYWORDS, source="patents")
    if not patent_comparison.empty:
        print(patent_comparison.to_string())

    print("\n\n--- PUBLICATION MONTHLY TRENDS ---")
    pub_comparison = compare_keywords(COMPARE_KEYWORDS, source="publications")
    if not pub_comparison.empty:
        print(pub_comparison.to_string())


if __name__ == "__main__":
    main()