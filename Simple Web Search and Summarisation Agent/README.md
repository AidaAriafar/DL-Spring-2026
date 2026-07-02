# AI Research Agent — Web Search & Summarization

A simple Python agent that takes a topic/question, plans a search strategy with a local LLM (via Ollama), searches the web with DuckDuckGo, crawls and cleans the resulting pages, deduplicates near-identical content, and produces a structured Markdown research report with sources and a chain-of-thought appendix.

---

## 1. Architecture

```
User Topic (string)
      │
      ▼
┌─────────────┐   LLM call: queries, num_sources, focus
│ planner.py  │──────────────────────────────────────────┐
└─────────────┘                                           │
      │ plan (dict, with fallback on LLM/JSON failure)     │
      ▼                                                    │
┌─────────────┐   DuckDuckGo search, retry + backoff       │
│ searcher.py │──────────────────────────────────────────► │
└─────────────┘                                            │
      │ list[url]                                          │
      ▼                                                     │
┌─────────────┐   Playwright headless Chromium              │
│ crawler.py  │──────────────────────────────────────────► │
└─────────────┘                                             │
      │ list[{url, html}]                                   │
      ▼                                                      │
┌──────────────┐  readability-lxml + BeautifulSoup            │
│ extractor.py │────────────────────────────────────────►  │
└──────────────┘                                             │
      │ (title, text), anti-bot pages filtered out            │
      ▼                                                       │
┌──────────────────┐  Jaccard similarity on paragraphs        │
│ deduplicator.py   │──────────────────────────────────────► │
└──────────────────┘                                          │
      │ clean, deduped text                                    │
      ▼                                                         │
┌──────────┐  accumulates pages under MAX_TOTAL_CONTEXT          │
│ main.py  │◄──────────────────────────────────────────────────┘
└──────────┘
      │ combined context (capped, per-page + global limits)
      ▼
┌────────────────┐  3-step "divide & conquer": intro → body → conclusion
│ summarizer.py   │  (3 separate LLM calls, each with its own prompt)
└────────────────┘
      │ report body (Markdown)
      ▼
report_<topic-slug>.md
  ├─ # Topic
  ├─ ## Summary
  ├─ ## Key Points
  ├─ ## Sources (title, URL, access date)
  └─ ## Appendix: Chain of Thought (plan JSON)
```

---

## 2. Project Structure

```
.
├── main.py             # orchestrates the pipeline end-to-end
├── config.py            # env-driven config (model, Ollama URL, context limits)
├── planner.py            # LLM call #1: search plan (queries, focus, num_sources)
├── searcher.py            # DuckDuckGo search with retry/backoff
├── crawler.py              # Playwright-based async crawling
├── extractor.py             # readability + BeautifulSoup text extraction
├── deduplicator.py           # Jaccard-similarity paragraph deduplication
├── summarizer.py               # LLM calls #2-4: intro / body / conclusion
├── test_agent.py                 # pytest suite (move into tests/, see §6)
├── requirements.txt
├── Dockerfile
├── .env.example
├── reports/
│   ├── report_topic1.md
│   └── report_topic2.md
└── README.md
```

---

## 3. Requirements

- Python 3.10+
- An Ollama-served local LLM (e.g. `llama3.2`, `mistral`, `phi3`)
- See `requirements.txt` for Python packages:
  `ddgs`, `playwright`, `beautifulsoup4`, `readability-lxml`, `litellm`, `pytest`, `lxml`

---

## 4. Setup — Option A: Local Machine

1. **Install Ollama** — download from [ollama.com/download](https://ollama.com/download).
2. **Pull a model:**
   ```bash
   ollama pull llama3.2
   ```
3. **Start the Ollama server** (usually starts automatically after install; otherwise):
   ```bash
   ollama serve
   ```
4. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   playwright install-deps
   ```
5. **Set up environment variables:**
   ```bash
   cp .env.example .env
   ```
6. **Run the agent:**
   ```bash
   python main.py "What is the impact of AI on renewable energy?"
   ```
   The report is written to `reports/report_<topic-slug>.md`.

---

## 5. Setup — Option B: Kaggle Notebook

Kaggle notebooks don't have Ollama pre-installed and don't allow background daemons by default, so the setup needs a few extra steps compared to a local machine. These are the cells used to get it running on Kaggle:

**Cell 1 — Python dependencies:**
```python
!pip install ddgs playwright beautifulsoup4 readability-lxml litellm pytest lxml
!playwright install chromium
!playwright install-deps
```

**Cell 2 — system packages required by the Ollama installer:**
```python
!apt-get update
!apt-get install -y zstd
```

**Cell 3 — install Ollama:**
```python
!curl -fsSL https://ollama.com/install.sh | sh
```

**Cell 4 — start the Ollama server in the background:**
```python
import subprocess
import time

# Start Ollama in the background — Kaggle has no init system,
# so it must be launched as a detached subprocess.
subprocess.Popen(["ollama", "serve"])
print("Ollama server is starting...")
time.sleep(5)  # give the server a few seconds to come up before pulling/calling it
print("Ready!")
```

**Cell 5 — pull the model:**
```python
!ollama pull llama3.2
```

**Cell 6 — run the agent:**
```python
!python main.py "What is the impact of AI on renewable energy?"
```

### Kaggle-specific notes
- The Ollama server and pulled model **do not persist** between sessions — cells 2–5 must be re-run every time you start a fresh Kaggle session/kernel.
- Keep `OLLAMA_BASE_URL` at its default (`http://localhost:11434`) on Kaggle — no need to override it, since Ollama runs inside the same kernel environment.
- If `ollama pull` hangs or times out, re-run cell 4 (server sometimes needs a moment longer than 5s) before retrying the pull.
- GPU acceleration for Ollama depends on the Kaggle accelerator setting (GPU T4 x2 / P100) — without it, generation will just be slower on CPU, not broken.

---

## 6. Setup — Option C: Docker

The included `Dockerfile` builds an image with Python, Playwright browsers, and the agent code — but it does **not** bundle Ollama itself. Ollama must be running on the **host machine**, and the container talks to it over `host.docker.internal`.

1. **On the host**, make sure Ollama is running and the model is pulled:
   ```bash
   ollama pull llama3.2
   ollama serve
   ```
2. **Build the image:**
   ```bash
   docker build -t research-agent .
   ```
3. **Run it (one-liner):**
   ```bash
   docker run --rm -v "$(pwd)/reports:/app/reports" research-agent python main.py "How are large language models changing software engineering?"
   ```
   - `-v "$(pwd)/reports:/app/reports"` mounts the reports folder so the output Markdown file is accessible on the host after the container exits.
   - The `Dockerfile` already sets `OLLAMA_BASE_URL=http://host.docker.internal:11434`.
   - **On Linux hosts**, `host.docker.internal` isn't resolved by default — add `--add-host=host.docker.internal:host-gateway` to the `docker run` command if you hit a connection error.

---

## 7. Configuration

Environment variables (see `.env.example`):

| Variable | Default | Purpose |
|---|---|---|
| `LLM_MODEL_NAME` | `ollama/llama3.2` | Model passed to LiteLLM. Change to switch models (e.g. `ollama/mistral`). |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Where Ollama is listening. Override for Docker (`host.docker.internal`) or a remote Ollama instance. |

No API keys are required since both DuckDuckGo search and Ollama are free/local.

---

## 8. Running Tests

```bash
pytest -v
```

Covers: HTML text extraction, planner JSON-failure fallback, paragraph deduplication (including short-paragraph filtering), global context-limit accumulation logic, and the empty-queries edge case in the searcher (regression test for a previously-fixed `ZeroDivisionError`).

---

## 9. Output Format

Each run produces `reports/report_<topic-slug>.md`:

```markdown
# <Topic>

## Summary
[Intro + Main Analysis + Conclusion, generated in three LLM passes]

## Key Points
- ...

## Sources
- [Title](URL) – accessed YYYY-MM-DD

## Appendix: Chain of Thought
```json
{ "queries": [...], "num_sources": 5, "focus": "...", "keywords": [...] }
```
```

---

## 10. Design Choices

- **Orchestration:** plain Python (no LangChain/CrewAI) — chosen for transparency and easier debugging within the assignment's scope, per the "recommended for simplicity" hint in the spec.
- **Summarization strategy:** the report body is generated via three separate LLM calls (intro, body, conclusion) rather than one large call, to reliably hit the length/structure requirements without relying on the model to self-regulate paragraph counts in a single pass.
- **Crawling:** async Playwright wrapped in a sync-safe `crawl_urls()` entry point, so it works whether or not an event loop is already running (relevant on Kaggle, which runs notebooks inside an existing loop).
