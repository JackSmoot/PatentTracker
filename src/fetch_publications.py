import requests
import time
import xml.etree.ElementTree as ET
from datetime import date, timedelta

# ── arXiv ────────────────────────────────────────────────────────────────────

ARXIV_BASE = "http://export.arxiv.org/api/query"
ARXIV_NS = "http://www.w3.org/2005/Atom"


def _fetch_arxiv_chunk(keyword: str, start: int, max_results: int = 100) -> list[dict]:
    """Fetch one page of arXiv results for a keyword."""
    params = {
        "search_query": f'all:"{keyword}"',
        "start": start,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending"
    }

    try:
        response = requests.get(ARXIV_BASE, params=params, timeout=30)
        if response.status_code != 200:
            print(f"    arXiv error {response.status_code}")
            return []

        root = ET.fromstring(response.content)
        ns = {"atom": ARXIV_NS}
        entries = root.findall("atom:entry", ns)

        results = []
        for entry in entries:
            # Extract fields
            arxiv_id = entry.find("atom:id", ns)
            title_el = entry.find("atom:title", ns)
            abstract_el = entry.find("atom:summary", ns)
            published_el = entry.find("atom:published", ns)

            authors = entry.findall("atom:author", ns)
            author_names = ", ".join([
                a.find("atom:name", ns).text
                for a in authors
                if a.find("atom:name", ns) is not None
            ])

            # Parse date - arXiv returns full ISO datetime
            pub_date = ""
            if published_el is not None and published_el.text:
                pub_date = published_el.text[:10]  # Just YYYY-MM-DD

            url = arxiv_id.text.strip() if arxiv_id is not None else ""
            # Convert http://arxiv.org/abs/XXXX to clean ID
            clean_id = f"arxiv:{url.split('/')[-1]}" if url else ""

            results.append({
                "pub_id": clean_id,
                "source": "arxiv",
                "title": (title_el.text or "").strip().replace("\n", " ") if title_el is not None else "",
                "abstract": (abstract_el.text or "").strip().replace("\n", " ") if abstract_el is not None else "",
                "date": pub_date,
                "authors": author_names,
                "venue": "arXiv",
                "citation_count": 0,
                "url": url
            })

        return results

    except Exception as e:
        print(f"    arXiv request failed: {e}")
        return []


def fetch_arxiv(keyword: str, start_date: str, end_date: str, max_results: int = 500) -> list[dict]:
    """
    Fetch papers from arXiv for a keyword within a date range.

    Args:
        keyword: Search term (searches title, abstract, all fields)
        start_date: Format 'YYYY-MM-DD'
        end_date: Format 'YYYY-MM-DD'
        max_results: Maximum total results to retrieve

    Returns:
        List of publication dictionaries
    """
    print(f"  [arXiv] Searching for: '{keyword}'")

    all_results = []
    seen_ids = set()
    start = 0
    page_size = 100

    start_dt = date.fromisoformat(start_date)
    end_dt = date.fromisoformat(end_date)

    while start < max_results:
        chunk = _fetch_arxiv_chunk(keyword, start, page_size)

        if not chunk:
            break

        # Filter by date and deduplicate
        new_count = 0
        stopped_early = False
        for paper in chunk:
            if not paper["pub_id"] or paper["pub_id"] in seen_ids:
                continue

            # Date filter
            if paper["date"]:
                paper_dt = date.fromisoformat(paper["date"])
                if paper_dt < start_dt:
                    # arXiv is sorted by date desc, so once we go past start_date we're done
                    stopped_early = True
                    break
                if paper_dt > end_dt:
                    continue

            seen_ids.add(paper["pub_id"])
            all_results.append(paper)
            new_count += 1

        if stopped_early or len(chunk) < page_size:
            break

        start += page_size
        time.sleep(3)  # arXiv asks for 3s between requests

    print(f"    → {len(all_results)} papers found")
    return all_results


# ── Semantic Scholar ──────────────────────────────────────────────────────────

SS_BASE = "https://api.semanticscholar.org/graph/v1/paper/search"
SS_FIELDS = "paperId,title,abstract,year,publicationDate,authors,venue,citationCount,externalIds,openAccessPdf"


def fetch_semantic_scholar(keyword: str, start_date: str, end_date: str, max_results: int = 500) -> list[dict]:
    """
    Fetch papers from Semantic Scholar for a keyword within a date range.

    Args:
        keyword: Search term
        start_date: Format 'YYYY-MM-DD'
        end_date: Format 'YYYY-MM-DD'
        max_results: Maximum total results to retrieve

    Returns:
        List of publication dictionaries
    """
    print(f"  [Semantic Scholar] Searching for: '{keyword}'")

    start_year = start_date[:4]
    end_year = end_date[:4]

    all_results = []
    seen_ids = set()
    offset = 0
    page_size = 100  # SS max per request

    start_dt = date.fromisoformat(start_date)
    end_dt = date.fromisoformat(end_date)

    while offset < max_results:
        params = {
            "query": keyword,
            "fields": SS_FIELDS,
            "limit": min(page_size, max_results - offset),
            "offset": offset,
            "year": f"{start_year}-{end_year}"
        }

        try:
            response = requests.get(SS_BASE, params=params, timeout=30)

            if response.status_code == 429:
                print("    Rate limited — waiting 30 seconds...")
                time.sleep(30)
                continue

            if response.status_code != 200:
                print(f"    Semantic Scholar error {response.status_code}: {response.text[:200]}")
                break

            data = response.json()
            papers = data.get("data") or []

            if not papers:
                break

            new_count = 0
            for paper in papers:
                paper_id = f"ss:{paper.get('paperId', '')}"
                if paper_id in seen_ids:
                    continue

                # Date handling - use publicationDate if available, fall back to year
                pub_date = paper.get("publicationDate") or ""
                if not pub_date and paper.get("year"):
                    pub_date = f"{paper['year']}-01-01"

                # Date filter
                if pub_date:
                    try:
                        paper_dt = date.fromisoformat(pub_date[:10])
                        if paper_dt < start_dt or paper_dt > end_dt:
                            continue
                    except ValueError:
                        pass

                seen_ids.add(paper_id)
                new_count += 1

                # Authors
                authors = paper.get("authors") or []
                author_names = ", ".join([a.get("name", "") for a in authors[:5]])
                if len(authors) > 5:
                    author_names += f" et al. (+{len(authors) - 5})"

                # URL - prefer open access PDF, fall back to SS page
                pdf = paper.get("openAccessPdf") or {}
                url = pdf.get("url") or f"https://www.semanticscholar.org/paper/{paper.get('paperId', '')}"

                all_results.append({
                    "pub_id": paper_id,
                    "source": "semantic_scholar",
                    "title": paper.get("title", "") or "",
                    "abstract": paper.get("abstract", "") or "",
                    "date": pub_date[:10] if pub_date else "",
                    "authors": author_names,
                    "venue": paper.get("venue", "") or "",
                    "citation_count": paper.get("citationCount", 0) or 0,
                    "url": url
                })

            offset += len(papers)

            if len(papers) < page_size:
                break

            time.sleep(1)  # Be polite to SS API

        except requests.exceptions.RequestException as e:
            print(f"    Request failed: {e}")
            break

    print(f"    → {len(all_results)} papers found")
    return all_results


# ── Combined fetcher ──────────────────────────────────────────────────────────

def fetch_publications(keyword: str, start_date: str, end_date: str, max_results: int = 500) -> list[dict]:
    """
    Fetch publications from both arXiv and Semantic Scholar.

    Args:
        keyword: Search term
        start_date: Format 'YYYY-MM-DD'
        end_date: Format 'YYYY-MM-DD'
        max_results: Max results per source

    Returns:
        Combined list of publication dictionaries
    """
    arxiv_results = fetch_arxiv(keyword, start_date, end_date, max_results)
    time.sleep(2)
    ss_results = fetch_semantic_scholar(keyword, start_date, end_date, max_results)

    combined = arxiv_results + ss_results
    print(f"  Total from both sources: {len(combined)} papers")
    return combined