import logging
import time
import random
from ddgs import DDGS

logger = logging.getLogger(__name__)


def _search_with_retry(query: str, max_results: int, max_retries: int = 3) -> list[dict]:
    for attempt in range(1, max_retries + 1):
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))
            if results:
                return results
            logger.warning(f"DDG returned 0 results for '{query}' (attempt {attempt}/{max_retries})")
        except Exception as e:
            logger.warning(f"DDG error for '{query}' (attempt {attempt}/{max_retries}): {type(e).__name__}: {e}")

        if attempt < max_retries:
            sleep_time = (2 ** attempt) + random.uniform(0, 1)
            logger.info(f"Retrying in {sleep_time:.1f}s...")
            time.sleep(sleep_time)

    return []


def search_queries(queries: list[str], max_total_sources: int = 5) -> list[str]:
    if not queries:
        logger.warning("No queries provided to search_queries; returning no results.")
        return []

    logger.info(f"Executing search for queries: {queries}")
    unique_urls = set()
    results = []

    per_query = max(1, max_total_sources // len(queries)) + 1

    for query in queries:
        if len(results) >= max_total_sources:
            break

        query_results = _search_with_retry(query, per_query)

        if not query_results:
            logger.error(f"All retries exhausted for query '{query}'.")
            continue

        for r in query_results:
            url = r.get("href")
            if url and url not in unique_urls:
                unique_urls.add(url)
                results.append(url)
            if len(results) >= max_total_sources:
                break

        if query != queries[-1]:
            time.sleep(random.uniform(1, 2))

    if not results:
        logger.error("No URLs found across all queries.")

    return results[:max_total_sources]
