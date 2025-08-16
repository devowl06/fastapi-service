from fastapi import FastAPI, Request, Query
from playwright.async_api import async_playwright
from markitdown import MarkItDown
from bs4 import BeautifulSoup
import tempfile
import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Welcome to the FastAPI Markdown Converter. To use this, hit the /fetch endpoint with a URL parameter. example: /fetch?url=https://example.com"}

@app.get("/fetch")
async def fetch_page(request: Request):
    """
    Fetch a webpage using Playwright and return its Markdown version.
    """
    # Full URL
    # url = str(request.url) # please note: use this for production and comment out the below logic for url
    url = request.query_params.get("url")
    if not url:
        return {"error": "Missing 'url' query parameter"}
    logger.info(f"Full URL: {url}")

    html = ""

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

    # Clean HTML with BeautifulSoup
    logger.info("Cleaning HTML with BeautifulSoup...")
    try:
        soup = BeautifulSoup(html, "lxml")
        
        # Remove completely useless/noisy tags
        for tag in soup(["script", "style", "noscript", "iframe"]):
            tag.decompose()

        # Replace <img> with alt text (or drop if no alt)
        for img in soup.find_all("img"):
            alt_text = img.get("alt") or "[Image]"
            img.replace_with(f"![{alt_text}]")

        # Drop inline SVGs entirely (too verbose, AI doesn’t need them)
        for svg in soup.find_all("svg"):
            svg.decompose()

        # Replace <video> with a placeholder
        for video in soup.find_all("video"):
            desc = video.get("title") or video.get("aria-label") or "Video content"
            video.replace_with(f"[Video: {desc}]")

        clean_html = str(soup)
    except Exception as e:
        logger.error(f"Error cleaning HTML: {e}")
        return {"error": "HTML cleaning failed"}

    # Convert HTML → Markdown
    logger.info("Converting cleaned HTML to Markdown...")
    tmp_file_path = None
    try:
        # Create a temporary file
        with tempfile.NamedTemporaryFile("w+", suffix=".html", delete=False, encoding="utf-8") as tmp_file:
            tmp_file.write(clean_html)
            tmp_file_path = tmp_file.name
            logger.info(f"Temporary HTML file created at {tmp_file_path}")

        # Convert the temporary HTML file to Markdown
        markitdown = MarkItDown()
        markdown_doc = markitdown.convert(tmp_file_path)
    except Exception as e:
        logger.error(f"Error converting HTML to Markdown: {e}")
        return {"error": f"Markdown conversion failed"}
    finally:
        if tmp_file_path and os.path.exists(tmp_file_path):
            try:
                os.remove(tmp_file_path)
                logger.info(f"Temporary file {tmp_file_path} removed.")
            except Exception as cleanup_err:
                logger.warning(f"Failed to remove temporary file {tmp_file_path}: {cleanup_err}")

    return {
        "url": url,
        "markdown": markdown_doc.text_content
    }