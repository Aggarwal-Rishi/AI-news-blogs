from django.core.management.base import BaseCommand
from pipeline.news_fetcher import fetch_latest_news

class Command(BaseCommand):
    help = 'Fetches the latest news entries from Google News RSS for the query "AI"'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Starting to fetch news..."))
        
        try:
            new_items = fetch_latest_news(limit=5)
            count = len(new_items)
            
            if count > 0:
                self.stdout.write(self.style.SUCCESS(f"Successfully fetched {count} new news items."))
                for item in new_items:
                    self.stdout.write(f"- {item.title}")
            else:
                self.stdout.write(self.style.WARNING("No new news items found."))
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"An unexpected error occurred: {e}"))
