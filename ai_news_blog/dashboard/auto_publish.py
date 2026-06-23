import datetime
import logging
from django.utils import timezone
from blog.models import BlogPost

logger = logging.getLogger(__name__)

def check_and_auto_publish():
    """
    Finds all BlogPost records with status "pending" where pending_since is more than 48 hours ago.
    Sets status to "published" and published_at to now.
    """
    logger.info("Checking for pending blog posts to auto-publish...")
    
    threshold_time = timezone.now() - datetime.timedelta(hours=48)
    overdue_posts = BlogPost.objects.filter(status='pending', pending_since__lte=threshold_time)
    overdue_count = overdue_posts.count()
    
    if overdue_count > 0:
        logger.info(f"Found {overdue_count} pending posts that have passed the 48-hour review window.")
        for post in overdue_posts:
            post.status = 'published'
            post.published_at = timezone.now()
            post.save()
            logger.info(f"Auto-published post: '{post.title}' (ID: {post.id})")
    else:
        logger.info("No pending posts are overdue for auto-publishing.")
        
    return overdue_count
