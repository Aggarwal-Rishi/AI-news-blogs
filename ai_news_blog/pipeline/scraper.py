import logging
import os
from playwright.sync_api import sync_playwright
from .models import RawNewsItem

# Allow sync ORM calls in async contexts (Playwright creates one)
os.environ["DJANGO_ALLOW_ASYNC_QUERY_RES_GETTER"] = "true"

logger = logging.getLogger(__name__)

def scrape_article(raw_news_item):
    """
    Scrapes the full article text from a RawNewsItem's link.
    Follows redirects and handles basic text extraction.
    """
    google_link = raw_news_item.google_news_link
    target_id = raw_news_item.id
    
    result = {
        'success': False,
        'resolved_url': None,
        'content': None,
        'status': 'scrape_failed'
    }

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            
            try:
                logger.info(f"Navigating to {google_link}")
                page.goto(google_link, timeout=15000, wait_until="networkidle")
                
                # Wait a bit more for dynamic content
                page.wait_for_timeout(2000)
                
                result['resolved_url'] = page.url
                logger.info(f"Resolved to {result['resolved_url']}")

                article_content = page.evaluate("""() => {
                    const article = document.querySelector('article');
                    if (article && article.innerText.split(/\\s+/).length > 200) return article.innerText;
                    
                    const main = document.querySelector('main');
                    if (main && main.innerText.split(/\\s+/).length > 200) return main.innerText;

                    const containers = Array.from(document.querySelectorAll('div, section'));
                    let bestContainer = null;
                    let maxParagraphs = 0;
                    
                    containers.forEach(c => {
                        const pCount = c.querySelectorAll('p').length;
                        if (pCount > maxParagraphs) {
                            maxParagraphs = pCount;
                            bestContainer = c;
                        }
                    });
                    
                    if (bestContainer) {
                        return Array.from(bestContainer.querySelectorAll('p'))
                            .map(p => p.innerText)
                            .filter(text => text.trim().length > 20)
                            .join('\\n\\n');
                    }
                    return null;
                }""")

                if article_content and len(article_content.split()) >= 200:
                    result['content'] = article_content
                    result['status'] = 'scraped'
                    result['success'] = True
                else:
                    logger.warning(f"Extracted content too short or missing for item {target_id}")

            except Exception as e:
                logger.error(f"Error during page execution for {google_link}: {e}")
            finally:
                browser.close()
    
    except Exception as e:
        logger.error(f"Playwright initialization error: {e}")

    # Perform database updates OUTSIDE the playwright context
    raw_news_item.resolved_article_url = result['resolved_url']
    raw_news_item.scraped_content = result['content']
    raw_news_item.status = result['status']
    raw_news_item.save()
    
    if result['success']:
        logger.info(f"Successfully scraped article {target_id}")
    
    return result['success']

def scrape_pending_items(target_count=5):
    """
    Fetches pending items and scrapes them until target_count successes are reached.
    Prioritizes 'carried_over' items first, ordered by oldest 'fetched_at'.
    """
    carried_over_items = RawNewsItem.objects.filter(status='carried_over').order_by('fetched_at')
    fetched_items = RawNewsItem.objects.filter(status='fetched').order_by('fetched_at')
    items = list(carried_over_items) + list(fetched_items)
    
    scraped_items = []
    success_count = 0
    
    for item in items:
        if success_count >= target_count:
            break
            
        success = scrape_article(item)
        if success:
            scraped_items.append(item)
            success_count += 1
            
    return scraped_items

