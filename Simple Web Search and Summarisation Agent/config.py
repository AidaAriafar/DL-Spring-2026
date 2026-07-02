import logging
import os
MODEL_NAME = os.getenv("LLM_MODEL_NAME", "ollama/llama3.2")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")


MAX_CHARS_PER_PAGE = 2000
MAX_TOTAL_CONTEXT = 12000


CRAWLER_TIMEOUT = 15000
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
