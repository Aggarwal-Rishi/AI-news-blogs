from django.core.management.base import BaseCommand
from pipeline.orchestrator import run_pipeline

class Command(BaseCommand):
    help = 'Runs the daily news fetching, scraping, blog writing, and image generation pipeline.'

    def handle(self, *args, **options):
        self.stdout.write("Starting daily news pipeline management command...")
        
        try:
            result = run_pipeline()
            
            self.stdout.write(self.style.SUCCESS("Daily pipeline execution completed successfully."))
            self.stdout.write(f"Fetched: {result['fetched']}")
            self.stdout.write(f"Scraped: {result['scraped']}")
            self.stdout.write(f"Blogs generated: {result['blogs']}")
            self.stdout.write(f"Images generated: {result['images']}")
            self.stdout.write(f"Carried over: {result['carried_over']}")
            
            if result['quota_exceeded']:
                self.stdout.write(self.style.WARNING("Pipeline terminated early due to Gemini API quota exception."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Pipeline execution failed with fatal error: {e}"))
