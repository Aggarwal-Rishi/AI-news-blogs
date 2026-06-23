import logging
from django.utils import timezone
from .models import RawNewsItem
from .news_fetcher import fetch_latest_news
from .scraper import scrape_pending_items
from .blog_writer import generate_blog, GeminiQuotaExceeded
from .image_generator import generate_image

logger = logging.getLogger(__name__)

def send_failure_notification(reason, processed_count, total_attempted):
    """
    Placeholder failure notification. Will be fully implemented in Step 9.
    """
    logger.error(
        f"[NOTIFICATION FAILURE] Reason: {reason}, "
        f"Processed: {processed_count}, Attempted: {total_attempted}"
    )

def run_pipeline():
    """
    Runs the daily news pipeline.
    """
    logger.info("Starting daily news pipeline run...")
    
    # 1. Check for carried over items
    carried_over_items = RawNewsItem.objects.filter(status='carried_over')
    carried_over_count = carried_over_items.count()
    logger.info(f"Found {carried_over_count} carried over items from previous runs.")

    # 2. If fewer than 5 total items available (carried-over + need to top up), fetch new
    to_fetch = 0
    fetched_count = 0
    if carried_over_count < 5:
        to_fetch = 5 - carried_over_count
        logger.info(f"Topping up with {to_fetch} new news items from Google News...")
        try:
            new_items = fetch_latest_news(limit=to_fetch)
            fetched_count = len(new_items)
            logger.info(f"Successfully fetched {fetched_count} new news items.")
        except Exception as e:
            logger.error(f"Error fetching news items: {e}")
            # We don't crash the whole run, we continue with whatever we have
    
    # 3. Scrape pending items (carried over first, then fetched, up to 5 target successes)
    logger.info("Scraping pending items...")
    scraped_items = []
    try:
        scraped_items = scrape_pending_items(target_count=5)
        scraped_count = len(scraped_items)
        logger.info(f"Scraped {scraped_count} items successfully.")
    except Exception as e:
        logger.error(f"Error during scraping: {e}")
        scraped_count = 0

    # 4. Generate blogs for successfully scraped items
    blogs_generated = 0
    images_generated = 0
    attempted_count = len(scraped_items)
    quota_exceeded = False
    
    for item in scraped_items:
        logger.info(f"Generating blog post for: '{item.title}'")
        try:
            blog_post = generate_blog(item)
            if blog_post:
                blogs_generated += 1
                logger.info(f"Blog post '{blog_post.title}' generated successfully.")
                
                # 5. Generate image
                logger.info("Generating featured image...")
                try:
                    if generate_image(blog_post):
                        images_generated += 1
                        logger.info(f"Featured image generated: {blog_post.featured_image_url}")
                    else:
                        logger.warning("Image generation failed.")
                except Exception as e:
                    logger.error(f"Unexpected error generating image: {e}")
            else:
                logger.error(f"Failed to generate blog post for item: {item.id}")
        except GeminiQuotaExceeded as e:
            logger.warning("Gemini API quota exceeded. Stopping blog generation immediately.")
            quota_exceeded = True
            
            # Mark remaining unprocessed items as 'carried_over'
            unprocessed_scraped = RawNewsItem.objects.filter(status='scraped')
            unprocessed_count = unprocessed_scraped.count()
            logger.info(f"Carrying over {unprocessed_count} unprocessed scraped items.")
            for unprocessed_item in unprocessed_scraped:
                unprocessed_item.status = 'carried_over'
                unprocessed_item.save()
                
            # Send notification (defined placeholder)
            try:
                send_failure_notification(
                    reason="gemini_quota_exceeded",
                    processed_count=blogs_generated,
                    total_attempted=attempted_count
                )
            except Exception as notification_error:
                logger.error(f"Failed to send failure notification: {notification_error}")
                
            break
        except Exception as e:
            logger.error(f"Unexpected error writing blog: {e}")

    # 6. Summary Logging
    carried_over_final_count = RawNewsItem.objects.filter(status='carried_over').count()
    logger.info("================== PIPELINE RUN SUMMARY ==================")
    logger.info(f"New items fetched:       {fetched_count}")
    logger.info(f"Items scraped successfully: {scraped_count}")
    logger.info(f"Blogs generated:          {blogs_generated}")
    logger.info(f"Images generated:         {images_generated}")
    logger.info(f"Items carried over (DB):  {carried_over_final_count}")
    logger.info("==========================================================")
    
    return {
        'fetched': fetched_count,
        'scraped': scraped_count,
        'blogs': blogs_generated,
        'images': images_generated,
        'carried_over': carried_over_final_count,
        'quota_exceeded': quota_exceeded
    }
