import logging
import json
import re
import sys
from datetime import date
import config
from planner import generate_plan
from searcher import search_queries
from crawler import crawl_urls
from extractor import extract_text
from deduplicator import deduplicate_paragraphs
from summarizer import generate_report_content
logger= logging.getLogger(__name__)

DEFAULT_TOPIC = "What is the impact of AI on renewable energy?"

def slugify(text: str, max_len: int = 40) -> str:
    slug = re.sub(r"[^\w\s-]", "", text.lower())
    slug = re.sub(r"[\s_-]+", "_", slug).strip("_")
    return slug[:max_len] or "topic"


def run_pipeline(topic: str, report_path: str | None = None) -> str:

    plan = generate_plan(topic)

    target_urls = search_queries(plan.get("queries", [topic]), plan.get("num_sources", 5))
    print(f"   [DEBUG] Found {len(target_urls)} URLs: {target_urls}")
    crawled_pages =crawl_urls(target_urls)
    processed_sources = []
    combined_text_chunks = []
    current_context_length = 0
    for page in crawled_pages:
        if current_context_length >= config.MAX_TOTAL_CONTEXT:
            logger.warning("Global context limit reached. Skipping remaining pages.")
            break
        title, text = extract_text(page["html"])
        if not text:
            continue
        clean_text = deduplicate_paragraphs(text)
        truncated_text = clean_text[:config.MAX_CHARS_PER_PAGE]
        if current_context_length + len(truncated_text) > config.MAX_TOTAL_CONTEXT:
            allowed_len = config.MAX_TOTAL_CONTEXT - current_context_length
            truncated_text = truncated_text[:allowed_len]

        processed_sources.append({"title": title, "url": page["url"]})
        combined_text_chunks.append(f"Source: {title}\n{truncated_text}")
        current_context_length += len(truncated_text)

    final_context = "\n\n---\n\n".join(combined_text_chunks)
    print(f"   [DEBUG] Processed {len(processed_sources)} sources, context length: {len(final_context)} chars")
    report_body = generate_report_content(topic, plan.get("focus", ""), final_context)
    logger.info("Assembling final Markdown report...")
    report_md = f"# {topic}\n\n{report_body}\n\n## Sources\n"
    for s in processed_sources:
        report_md += f"- [{s['title']}]({s['url']}) – accessed {date.today().isoformat()}\n"

    report_md += "\n## Appendix: Chain of Thought\n"
    safe_plan = {k: v for k, v in plan.items() if k in ["queries", "focus", "num_sources", "keywords"]}
    report_md += f"```json\n{json.dumps(safe_plan, indent=2)}\n```\n"

    if report_path is None:
        report_path = f"reports/report_{slugify(topic)}.md"

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_md)
    return report_path

def main():
    topic =sys.argv[1] if len(sys.argv) > 1 else DEFAULT_TOPIC
    run_pipeline(topic)


if __name__ == "__main__":
    main()
