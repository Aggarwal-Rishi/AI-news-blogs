from django.db import models
from blog.models import BlogPost

class RawNewsItem(models.Model):
    STATUS_CHOICES = [
        ('fetched', 'Fetched'),
        ('scraped', 'Scraped'),
        ('scrape_failed', 'Scrape Failed'),
        ('written', 'Written'),
        ('carried_over', 'Carried Over'),
    ]

    title = models.CharField(max_length=300)
    google_news_link = models.URLField()
    resolved_article_url = models.URLField(null=True, blank=True)
    published_date = models.DateTimeField(null=True, blank=True)
    scraped_content = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='fetched')
    fetched_at = models.DateTimeField(auto_now_add=True)
    linked_blog_post = models.ForeignKey(BlogPost, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.title
