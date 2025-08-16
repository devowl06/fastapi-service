from fastapi import FastAPI, Request, Query
from pydantic import BaseModel
from playwright.async_api import async_playwright
from markitdown import MarkItDown
import asyncio
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI()

@app.get("/fetch")
async def fetch_page(request: Request):
    """
    Fetch a webpage using Playwright and return its Markdown version.
    """
    # Full URL
    # url = str(request.url)
    url = request.query_params.get("url")
    if not url:
        return {"error": "Missing 'url' query parameter"}
    logger.info(f"Full URL: {url}")

    # Launch headless browser
    async with async_playwright() as p:
        logger.info("Launching Chromium...")
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        try:
            logger.info(f"Navigating to {url}")
            await page.goto(url, timeout=15000)  # 15s timeout
            logger.info(f"Navigation to {url} completed.")
            html = await page.content()
            logger.info(f"Fetched HTML content from {url} (length={len(html)} chars)")
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            await browser.close()
            return {"error": str(e)}

        await browser.close()
        logger.info("Browser closed successfully.")

    # Convert HTML → Markdown
    logger.info("Converting HTML to Markdown...")

    try:
        markitdown = MarkItDown()
        markdown_doc = markitdown.convert(html)
    except Exception as e:
        logger.error(f"Error converting HTML to Markdown: {e}")
        return {"error": f"Markdown conversion failed: {str(e)}"}

    return {
        "url": url,
        "markdown": markdown_doc.text_content
    }
