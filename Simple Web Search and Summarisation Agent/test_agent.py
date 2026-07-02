import pytest
from unittest.mock import patch

from extractor import extract_text
from planner import generate_plan
from deduplicator import deduplicate_paragraphs
from searcher import search_queries

def test_extract_text():
    sample_html = """
    <html><head><title>Test Page</title></head>
    <body><article><p>This is the main content.</p></article></body></html>
    """
    title, text = extract_text(sample_html)
    assert title == "Test Page"
    assert "This is the main content." in text

@patch("planner.completion")
def test_planner_fallback(mock_completion):
    mock_completion.side_effect = Exception("LLM Error")
    plan = generate_plan("Test Topic")

    assert isinstance(plan, dict)
    assert "queries" in plan
    assert plan["queries"][0]== "Test Topic"
    assert plan["num_sources"]== 5


def test_deduplicate_paragraphs():

    text =(
        "This is a long paragraph about renewable energy and AI systems today.\n"
        "This is a long paragraph about renewable energy and AI systems now.\n"
        "A completely unrelated paragraph discussing classical music history in depth."
    )
    result = deduplicate_paragraphs(text, threshold=0.7)
    paragraphs= [p for p in result.split("\n\n") if p.strip()]

    assert len(paragraphs)== 2
    assert any("classical music" in p for p in paragraphs)
    assert sum("renewable energy" in p for p in paragraphs)== 1

def test_deduplicate_paragraphs_filters_short_lines():
    text = "Too short\nAlso short\nThis paragraph is definitely long enough to survive filtering."
    result= deduplicate_paragraphs(text)
    assert "Too short" not in result
    assert "definitely long enough" in result


def test_context_limits():
    text1= "A" * 1500
    text2 ="B" * 1000
    max_limit= 2000
    current_length= 0
    final_text= ""
    for t in [text1, text2]:
        if current_length + len(t) > max_limit:
            allowed = max_limit - current_length
            final_text += t[:allowed]
            current_length += allowed
        else:
            final_text += t
            current_length+= len(t)
    assert len(final_text) == 2000
    assert final_text.count("A")== 1500
    assert final_text.count("B") ==500

def test_search_queries_empty_list_returns_empty():
    assert search_queries([]) == []
