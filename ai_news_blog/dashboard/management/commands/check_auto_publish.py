from django.core.management.base import BaseCommand
from dashboard.auto_publish import check_and_auto_publish

class Command(BaseCommand):
    help = 'Finds and publishes pending blog posts that are older than 48 hours.'

    def handle(self, *args, **options):
        self.stdout.write("Running auto-publish verification checks...")
        try:
            published_count = check_and_auto_publish()
            self.stdout.write(self.style.SUCCESS(f"Auto-publish check complete. Published: {published_count} posts."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Auto-publish verification check failed: {e}"))
