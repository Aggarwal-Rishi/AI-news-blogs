from django.core.management.base import BaseCommand
from pipeline.models import RawNewsItem
from pipeline.blog_writer import generate_blog, GeminiQuotaExceeded
from pipeline.image_generator import generate_image

class Command(BaseCommand):
    help = 'Generates blog posts and featured images'

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=1, help='Number of articles to process')

    def handle(self, *args, **options):
        limit = options['limit']
        scraped_items = RawNewsItem.objects.filter(status='scraped')[:limit]
        
        if not scraped_items.exists():
            self.stdout.write(self.style.WARNING("No scraped news items found."))
            return

        for item in scraped_items:
            self.stdout.write(f"Generating blog for: {item.title}")
            try:
                blog_post = generate_blog(item)
                if blog_post:
                    self.stdout.write(self.style.SUCCESS(f"Generated blog: {blog_post.title}"))
                    
                    self.stdout.write("Generating featured image...")
                    if generate_image(blog_post):
                        self.stdout.write(self.style.SUCCESS(f"Generated image: {blog_post.featured_image_url}"))
                    else:
                        self.stdout.write(self.style.WARNING("Failed to generate image."))
                else:
                    self.stdout.write(self.style.ERROR(f"Failed to generate blog for item {item.id}"))
            except GeminiQuotaExceeded:
                self.stdout.write(self.style.ERROR("Gemini quota exceeded."))
                break
