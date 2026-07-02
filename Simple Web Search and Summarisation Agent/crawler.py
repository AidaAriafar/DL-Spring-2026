import asyncio
import logging
from playwright.async_api import async_playwright
import config

logger = logging.getLogger(__name__)

async def _crawl_urls_async(urls: list[str]) -> list[dict]:
    logger.info(f"Starting crawl for {len(urls)} URLs...")
    crawled_pages= []

    async with async_playwright() as p:
        browser= await p.chromium.launch(headless=True)
        context =await browser.new_context(user_agent=config.USER_AGENT)

        for url in urls:
            page =None
            try:
                page = await context.new_page()
                await page.goto(url, timeout=config.CRAWLER_TIMEOUT, wait_until="domcontentloaded")
                try:
                    await page.wait_for_load_state("networkidle", timeout=3000)
                except Exception:
                    pass

                final_url = page.url
                html_content = await page.content()

                crawled_pages.append({"url": final_url, "html": html_content})
                logger.info(f"Successfully fetched: {final_url}")
            except Exception as e:
                logger.warning(f"Failure crawling {url}: {e}")
            finally:
                if page:
                    await page.close()

        await browser.close()
    return crawled_pages


def crawl_urls(urls: list[str]) -> list[dict]:
    try:
        return asyncio.run(_crawl_urls_async(urls))
    except RuntimeError:
        import concurrent.futures
        def _run_in_new_loop():
            return asyncio.run(_crawl_urls_async(urls))
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_run_in_new_loop)
            return future.result()
