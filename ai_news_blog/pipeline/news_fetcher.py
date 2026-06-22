import feedparser
import logging
from dateutil import parser
from .models import RawNewsItem

logger = logging.getLogger(__name__)

def fetch_latest_news(limit=5):
    """
    Fetches the latest news from Google News RSS for the query 'AI'.
    Returns a list of newly created RawNewsItem objects.
    """
    rss_url = "https://news.google.com/rss/search?q=AI&hl=en-US&gl=US&ceid=US:en"
    
    try:
        feed = feedparser.parse(rss_url)
    except Exception as e:
        logger.error(f"Failed to fetch or parse RSS feed: {e}")
        return []

    if feed.get('bozo', 0) == 1:
        logger.warning(f"RSS feed parsing encountered a non-fatal error: {feed.get('bozo_exception')}")

    entries = feed.entries[:limit]
    new_items = []

    for entry in entries:
        link = entry.get('link')
        title = entry.get('title')
        published_str = entry.get('published')
        
        # Parse published date
        published_date = None
        if published_str:
            try:
                published_date = parser.parse(published_str)
            except (ValueError, TypeError):
                logger.warning(f"Could not parse date: {published_str}")

        # Check for duplicates
        if not RawNewsItem.objects.filter(google_news_link=link).exists():
            item = RawNewsItem.objects.create(
                title=title,
                google_news_link=link,
                published_date=published_date,
                status='fetched'
            )
            new_items.append(item)
            logger.info(f"Fetched new item: {title}")
        else:
            logger.debug(f"Skipping duplicate item: {title}")

    return new_items
