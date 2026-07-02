import json
import logging
from litellm import completion
import config

logger = logging.getLogger(__name__)
def generate_plan(topic: str) -> dict:
    logger.info("Generating structured search plan...")
    prompt = f"""
    You are an AI research planner. Analyze this topic: '{topic}'
    Return ONLY a valid JSON object. Do not include markdown formatting.
    {{
        "queries": ["3 distinct search queries"],
        "num_sources": 5,
        "keywords": ["keyword1", "keyword2", "keyword3"],
        "focus": "Brief sentence on what to prioritize"
    }}
    """
    try:
        response =completion(
            model=config.MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            api_base=config.OLLAMA_BASE_URL
        )
        content = response.choices[0].message.content.strip()

        if content.startswith("```json"):
            content= content[7:]
        if content.endswith("```"):
            content = content[:-3]

        content = content.strip()
        plan = json.loads(content)

        if not plan.get("queries"):
            logger.warning("LLM returned empty/missing 'queries'; using topic as fallback query.")
            plan["queries"] = [topic]
        if not plan.get("num_sources"):
            plan["num_sources"] = 5

        return plan
    except json.JSONDecodeError as e:
        logger.error(f"Planning failed: LLM returned invalid JSON: {e}")
    except Exception as e:
        logger.error(f"Planning failed: {e}")
    return {
        "queries": [topic],
        "num_sources": 5,
        "focus": "General overview",
        "keywords": []
    }
