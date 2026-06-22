from django.test import TestCase
from .news_fetcher import fetch_latest_news
from .models import RawNewsItem

class NewsFetcherTest(TestCase):
    def test_fetch_latest_news_returns_items(self):
        """Test that fetch_latest_news returns up to 5 items and creates RawNewsItem records."""
        # Note: This makes a real network request. 
        # In a production environment, we would mock the feedparser.parse call.
        new_items = fetch_latest_news(limit=5)
        
        # Check that we got a list
        self.assertIsInstance(new_items, list)
        
        # We can't guarantee how many items are new, but it should be between 0 and 5
        self.assertLessEqual(len(new_items), 5)
        
        # Check that items were actually created in the DB
        # If any were returned, they must exist in the DB
        for item in new_items:
            self.assertTrue(RawNewsItem.objects.filter(id=item.id).exists())
            self.assertEqual(item.status, 'fetched')

    def test_fetch_latest_news_duplicates(self):
        """Test that calling fetch_latest_news twice doesn't create duplicate items."""
        # First call
        initial_items = fetch_latest_news(limit=5)
        
        # Second call should find 0 new items (assuming the RSS feed hasn't updated in seconds)
        second_items = fetch_latest_news(limit=5)
        self.assertEqual(len(second_items), 0)
