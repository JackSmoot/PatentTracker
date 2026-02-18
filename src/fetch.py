import requests
import time
import os
from datetime import date, timedelta
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://api.uspto.gov/api/v1/patent/applications/search"


def _week_chunks(start_date: str, end_date: str):
    """Generate weekly (start, end) pairs between two dates."""
    start = date.fromisoformat(start_date)
    end = date.fromisoformat(end_date)
    current = start
    while current <= end:
        chunk_end = min(current + timedelta(days=6), end)
        yield current.isoformat(), chunk_end.isoformat()
        current += timedelta(days=7)


def _fetch_chunk(keyword: str, chunk_start: str, chunk_end: str, headers: dict) -> list[dict]:
    """Fetch all results for a single date chunk (one month)."""
    patents = []
    seen_ids = set()
    offset = 0
    page_size = 25

    while True:
        params = {
            "q": (
                f'applicationMetaData.inventionTitle:"{keyword}" AND '
                f'applicationMetaData.filingDate:[{chunk_start} TO {chunk_end}]'
            ),
            "start": offset,
            "rows": page_size,
            "sort": "applicationMetaData.filingDate asc"
        }

        try:
            response = requests.get(BASE_URL, headers=headers, params=params, timeout=30)

            if response.status_code == 429:
                print("    Rate limited — waiting 15 seconds...")
                time.sleep(15)
                continue

            if response.status_code != 200:
                print(f"    Error {response.status_code}: {response.text[:200]}")
                break

            data = response.json()
            results = data.get("patentFileWrapperDataBag") or []

            if not results:
                break

            new_this_page = 0
            for app in results:
                app_id = str(app.get("applicationNumberText", "") or "")
                if app_id in seen_ids:
                    continue
                seen_ids.add(app_id)
                new_this_page += 1

                meta = app.get("applicationMetaData") or {}
                title = meta.get("inventionTitle", "") or ""
                filing_date = meta.get("filingDate", "") or meta.get("effectiveFilingDate", "") or ""

                applicants = meta.get("applicantBag") or []
                assignee = ""
                if applicants:
                    assignee = applicants[0].get("applicantNameText", "") or ""
                if not assignee:
                    assignee = meta.get("firstApplicantName", "") or ""

                cpcs = meta.get("cpcClassificationBag") or []
                cpc_codes = ", ".join([
                    c.get("cpcClassificationSymbolText", "")
                    for c in cpcs if isinstance(c, dict)
                ])

                patents.append({
                    "patent_id": app_id,
                    "patent_title": title,
                    "patent_abstract": "",
                    "patent_date": filing_date,
                    "assignee_organization": assignee,
                    "cpc_codes": cpc_codes
                })

            if len(results) < page_size or new_this_page == 0:
                break

            offset += page_size
            time.sleep(0.3)

        except requests.exceptions.RequestException as e:
            print(f"    Request failed: {e}")
            break

    return patents


def fetch_patents(keyword: str, start_date: str, end_date: str, max_results: int = 1000) -> list[dict]:
    """
    Fetch patent applications from USPTO ODP, chunked by month to work around
    the API's ~25 result per query limitation.

    Args:
        keyword: Search term for invention titles
        start_date: Format 'YYYY-MM-DD'
        end_date: Format 'YYYY-MM-DD'
        max_results: Maximum total results across all chunks

    Returns:
        List of patent dictionaries normalized for our database schema
    """
    api_key = os.getenv("USPTO_API_KEY")
    if not api_key:
        raise ValueError("USPTO_API_KEY not found. Add it to your .env file.")

    headers = {
        "X-API-KEY": api_key,
        "Accept": "application/json"
    }

    all_patents = []
    all_ids = set()

    print(f"Searching USPTO ODP for: '{keyword}' between {start_date} and {end_date}")
    print("Strategy: fetching month by month to maximize coverage\n")

    for chunk_start, chunk_end in _week_chunks(start_date, end_date):
        if len(all_patents) >= max_results:
            print(f"  Reached max_results limit ({max_results}), stopping.")
            break

        print(f"  Chunk {chunk_start} to {chunk_end}...")
        chunk_results = _fetch_chunk(keyword, chunk_start, chunk_end, headers)

        new_records = [p for p in chunk_results if p["patent_id"] not in all_ids]
        for p in new_records:
            all_ids.add(p["patent_id"])

        all_patents.extend(new_records)
        print(f"    → {len(new_records)} new records (running total: {len(all_patents)})")
        time.sleep(0.5)

    print(f"\nTotal patents fetched: {len(all_patents)}")
    return all_patents