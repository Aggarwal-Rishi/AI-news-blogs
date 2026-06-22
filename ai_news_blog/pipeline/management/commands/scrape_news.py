import os
os.environ["DJANGO_ALLOW_ASYNC_QUERY_SET_GETTER"] = "true"

from django.core.management.base import BaseCommand
from pipeline.scraper import scrape_pending_items

class Command(BaseCommand):
    help = 'Scrapes the full text content of fetched news items using Playwright'

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=5, help='Target number of articles to successfully scrape')

    def handle(self, *args, **options):
        limit = options['limit']
        self.stdout.write(self.style.NOTICE(f"Starting to scrape up to {limit} articles..."))
        
        try:
            scraped_items = scrape_pending_items(target_count=limit)
            success_count = len(scraped_items)
            
            if success_count > 0:
                self.stdout.write(self.style.SUCCESS(f"Successfully scraped {success_count} articles."))
                for item in scraped_items:
                    self.stdout.write(f"- {item.title[:60]}... ({len(item.scraped_content.split())} words)")
            else:
                self.stdout.write(self.style.WARNING("No articles were successfully scraped."))
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"An unexpected error occurred: {e}"))
