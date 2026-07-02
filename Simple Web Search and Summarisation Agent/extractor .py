import logging
from bs4 import BeautifulSoup
from readability import Document
logger= logging.getLogger(__name__)
def extract_text(html_content: str) -> tuple[str, str]:
    try:
        doc= Document(html_content)
        title =doc.title()
        bot_phrases = ["Just a moment...", "Checking your browser...", "Attention Required!", "Cloudflare"]
        if any(phrase in title for phrase in bot_phrases):
            logger.warning(f"Blocked by anti-bot protection, skipping: {title}")
            return title, "" 
        clean_html = doc.summary()
        soup= BeautifulSoup(clean_html, 'html.parser')
        text =soup.get_text(separator='\n', strip=True)
        return title, text
    except Exception as e:
        logger.warning(f"Text extraction failed: {e}")
        return "Unknown Title", ""
