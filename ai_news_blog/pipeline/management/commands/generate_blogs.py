from django.core.management.base import BaseCommand
from pipeline.models import RawNewsItem
from pipeline.blog_writer import generate_blog, GeminiQuotaExceeded

class Command(BaseCommand):
    help = 'Generates blog posts from scraped news items using Gemini AI'

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=1, help='Number of articles to process')

    def handle(self, *args, **options):
        limit = options['limit']
        scraped_items = RawNewsItem.objects.filter(status='scraped')[:limit]
        
        if not scraped_items.exists():
            self.stdout.write(self.style.WARNING("No scraped news items found. Please run 'scrape_news' first."))
            return

        for item in scraped_items:
            self.stdout.write(f"Generating blog for: {item.title}")
            try:
                blog_post = generate_blog(item)
                if blog_post:
                    self.stdout.write(self.style.SUCCESS(f"Successfully generated blog: {blog_post.title} (ID: {blog_post.id})"))
                else:
                    self.stdout.write(self.style.ERROR(f"Failed to generate blog for item {item.id}"))
            except GeminiQuotaExceeded:
                self.stdout.write(self.style.ERROR("Gemini API quota exceeded. Stopping generation."))
                break
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error processing item {item.id}: {e}"))
