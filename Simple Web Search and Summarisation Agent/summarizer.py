import logging
import re
from litellm import completion
import config

logger = logging.getLogger(__name__)
_LEAKED_INSTRUCTION_RE = re.compile(r"^\s*\[[^\]\n]{0,120}\]\s*\n*", re.IGNORECASE)

def _strip_leaked_instructions(text: str) -> str:
    cleaned = _LEAKED_INSTRUCTION_RE.sub("", text, count=1)
    return cleaned.strip()

def _call_llm(prompt: str) -> str:
    try:
        response = completion(
            model=config.MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            api_base=config.OLLAMA_BASE_URL,
            max_tokens=1500,
        )
        raw_text = response.choices[0].message.content.strip()
        return _strip_leaked_instructions(raw_text)
    except Exception as e:
        logger.error(f"LLM Call Error: {e}")
        return ""


def generate_report_content(topic: str, focus: str, text_data: str) -> str:
    prompt_intro = f"""
You are writing a professional technical report.
Topic:
{topic}
Write ONLY the Introduction and Background.

Requirements:
 Use ONLY the information found in Context Data.
 Never use outside knowledge.
 If something is missing from the Context, simply omit it.
 Do NOT invent examples, numbers, model names or organizations.
Avoid generic AI-style introductions such as:
  "In today's world..."
  "As technology evolves..."
  "As we navigate..."
  "The rapid growth..."
Begin immediately with the topic itself.

Write exactly TWO detailed paragraphs.
Target length:
160-180 words.
Return ONLY the paragraphs.
Context Data:

{text_data}
"""
    logger.info("Generating Part 1: Introduction...")
    intro_text = _call_llm(prompt_intro)
    prompt_body = f"""
You are continuing the same report.

Topic:
{topic}

The Introduction has already been written.

Previously written Introduction:

{intro_text}

Now write ONLY the Main Analysis.

Requirements:

Do NOT repeat information already stated.
Expand the discussion.
Focus on:

{focus}

Use ONLY Context Data.

Never invent:

facts
numbers
statistics
percentages
 organizations
 model names

unless explicitly present in Context.

Cover:

mechanisms
 evidence
 examples
 challenges

Write exactly THREE detailed paragraphs.

Target length:
320-380 words.

Return ONLY the paragraphs.

Context Data:

{text_data}
"""
    logger.info("Generating Part 2: Main Body...")
    body_text = _call_llm(prompt_body)
    prompt_conclusion = f"""
You are finishing the report.

Topic:

{topic}

Current report:

{intro_text}

{body_text}

Now write the final conclusion.

Requirements:

Summarize the report.
Do NOT introduce any new information.
 Do NOT repeat paragraphs verbatim.
Use ONLY information already written.
 Never invent facts.
 Never invent statistics.
 Never invent product names.
 Never invent company names.

Write ONE paragraph.

Target length:
90-120 words.

Then output:

## Key Points

Write exactly 6-8 bullet points.

Rules:

Every bullet must describe a DIFFERENT finding.
Do not repeat ideas.
Do not introduce new information.
Extract only from the report.
Do NOT output:
Sources

Appendix

Conclusion heading
Markdown title

Any bracketed text.

Return ONLY:
<paragraph>

## Key Points

- ...
"""
    logger.info("Generating Part 3: Conclusion and Key Points...")
    conclusion_text = _call_llm(prompt_conclusion)
    if not intro_text or not body_text or not conclusion_text:
        return "## Summary\nGeneration failed due to LLM error.\n\n## Key Points\n- Error"

    final_report = f"## Summary\n\n{intro_text}\n\n{body_text}\n\n{conclusion_text}"
    final_report = re.sub(
        r"\n?\[.*?Write.*?\]\n?",
        "",
        final_report,
        flags=re.IGNORECASE,
    )
    final_report = re.sub(
        r"\n{3,}",
        "\n\n",
        final_report,
    )

    word_count = len(final_report.split())
    if word_count < 500:
        logger.warning(
            f"Summary too short ({word_count} words). Consider regenerating."
        )

    return final_report