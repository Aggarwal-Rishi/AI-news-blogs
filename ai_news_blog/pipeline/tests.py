from django.test import TestCase
from unittest.mock import patch, MagicMock
from blog.models import BlogPost
from dashboard.models import SystemNotification
from .news_fetcher import fetch_latest_news
from .models import RawNewsItem
from .image_generator import build_image_prompt, generate_image, regenerate_image
from .orchestrator import run_pipeline
from .blog_writer import GeminiQuotaExceeded



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

class ImageGeneratorTest(TestCase):
    def setUp(self):
        self.blog_post = BlogPost.objects.create(
            title="Test AI Blog Title",
            content="Some body content.",
            excerpt="A short summary of the AI blog.",
            featured_image_url="",
            status="pending",
            source_url="https://example.com/source",
            source_news_title="Source News Title"
        )

    @patch('pipeline.image_generator.client')
    def test_build_image_prompt_with_gemini(self, mock_client):
        # Mock client behavior
        mock_response = MagicMock()
        mock_response.text = "A cinematic shot of a futuristic robot, high-tech, cinematic lighting"
        mock_client.models.generate_content.return_value = mock_response

        prompt = build_image_prompt(self.blog_post)
        self.assertEqual(prompt, "A cinematic shot of a futuristic robot, high-tech, cinematic lighting")
        mock_client.models.generate_content.assert_called_once()

    @patch('pipeline.image_generator.client', None)
    def test_build_image_prompt_fallback(self):
        # If client is None, it should fall back to a default prompt
        prompt = build_image_prompt(self.blog_post)
        self.assertIn("Test AI Blog Title", prompt)

    @patch('pipeline.image_generator.requests.get')
    @patch('pipeline.image_generator.build_image_prompt')
    def test_generate_image_success(self, mock_build_prompt, mock_get):
        mock_build_prompt.return_value = "robot visual scene"
        
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {'Content-Type': 'image/png'}
        mock_get.return_value = mock_response

        success = generate_image(self.blog_post)
        
        self.assertTrue(success)
        self.blog_post.refresh_from_db()
        self.assertIn("https://image.pollinations.ai/prompt/robot%20visual%20scene", self.blog_post.featured_image_url)

    @patch('pipeline.image_generator.requests.get')
    @patch('pipeline.image_generator.build_image_prompt')
    def test_generate_image_failure_retry_success(self, mock_build_prompt, mock_get):
        mock_build_prompt.return_value = "robot visual scene"
        
        # Mock first call failing, second call succeeding
        mock_fail_response = MagicMock()
        mock_fail_response.status_code = 500
        
        mock_success_response = MagicMock()
        mock_success_response.status_code = 200
        mock_success_response.headers = {'Content-Type': 'image/jpeg'}
        
        mock_get.side_effect = [mock_fail_response, mock_success_response]

        success = generate_image(self.blog_post)
        
        self.assertTrue(success)
        self.assertEqual(mock_get.call_count, 2)
        self.blog_post.refresh_from_db()
        self.assertIn("Abstract%20high-tech%20futuristic%20background", self.blog_post.featured_image_url)

    @patch('pipeline.image_generator.requests.get')
    @patch('pipeline.image_generator.build_image_prompt')
    def test_generate_image_complete_failure(self, mock_build_prompt, mock_get):
        mock_build_prompt.return_value = "robot visual scene"
        
        # Both calls fail
        mock_fail_response = MagicMock()
        mock_fail_response.status_code = 500
        mock_get.return_value = mock_fail_response

        success = generate_image(self.blog_post)
        
        self.assertFalse(success)
        self.assertEqual(mock_get.call_count, 2)
        self.blog_post.refresh_from_db()
        self.assertEqual(self.blog_post.featured_image_url, "")

class PipelineOrchestratorTest(TestCase):
    def setUp(self):
        RawNewsItem.objects.all().delete()
        BlogPost.objects.all().delete()

    @patch('pipeline.orchestrator.fetch_latest_news')
    @patch('pipeline.orchestrator.scrape_pending_items')
    @patch('pipeline.orchestrator.generate_blog')
    @patch('pipeline.orchestrator.generate_image')
    def test_run_pipeline_success_no_carried_over(self, mock_generate_image, mock_generate_blog, mock_scrape_pending_items, mock_fetch_latest_news):
        # Mocks
        mock_fetch_latest_news.return_value = [
            RawNewsItem(title="News 1", google_news_link="http://1"),
            RawNewsItem(title="News 2", google_news_link="http://2"),
        ]
        
        item1 = RawNewsItem.objects.create(title="News 1", google_news_link="http://1", status="fetched")
        item2 = RawNewsItem.objects.create(title="News 2", google_news_link="http://2", status="fetched")
        
        item1.status = 'scraped'
        item1.scraped_content = 'content 1'
        item1.save()
        
        item2.status = 'scraped'
        item2.scraped_content = 'content 2'
        item2.save()
        
        mock_scrape_pending_items.return_value = [item1, item2]
        
        bp1 = BlogPost.objects.create(title="Blog 1", source_news_title="News 1")
        bp2 = BlogPost.objects.create(title="Blog 2", source_news_title="News 2")
        mock_generate_blog.side_effect = [bp1, bp2]
        
        mock_generate_image.return_value = True
        
        # Run
        result = run_pipeline()
        
        # Verify
        mock_fetch_latest_news.assert_called_once_with(limit=5)
        mock_scrape_pending_items.assert_called_once_with(target_count=5)
        self.assertEqual(mock_generate_blog.call_count, 2)
        self.assertEqual(mock_generate_image.call_count, 2)
        
        self.assertEqual(result['fetched'], 2)
        self.assertEqual(result['scraped'], 2)
        self.assertEqual(result['blogs'], 2)
        self.assertEqual(result['images'], 2)
        self.assertEqual(result['carried_over'], 0)
        self.assertFalse(result['quota_exceeded'])

    @patch('pipeline.orchestrator.fetch_latest_news')
    @patch('pipeline.orchestrator.scrape_pending_items')
    @patch('pipeline.orchestrator.generate_blog')
    @patch('pipeline.orchestrator.generate_image')
    @patch('pipeline.orchestrator.send_failure_notification')
    def test_run_pipeline_quota_exceeded(self, mock_notify, mock_generate_image, mock_generate_blog, mock_scrape_pending_items, mock_fetch_latest_news):
        # Create 2 carried over items in DB
        for i in range(2):
            RawNewsItem.objects.create(title=f"Carried {i}", google_news_link=f"http://c{i}", status="carried_over")
            
        # Top up expects limit=3
        mock_fetch_latest_news.return_value = [
            RawNewsItem(title="New 1", google_news_link="http://n1"),
            RawNewsItem(title="New 2", google_news_link="http://n2"),
            RawNewsItem(title="New 3", google_news_link="http://n3"),
        ]
        
        # Create 4 scraped items for scraping mock output
        scraped_items = []
        for i in range(4):
            item = RawNewsItem.objects.create(title=f"Scraped {i}", google_news_link=f"http://s{i}", status="scraped", scraped_content="some content")
            scraped_items.append(item)
            
        mock_scrape_pending_items.return_value = scraped_items
        
        bp1 = BlogPost.objects.create(title="Blog 0", source_news_title="Scraped 0")
        
        def generate_blog_side_effect(item):
            if item.title == "Scraped 0":
                item.status = "written"
                item.save()
                return bp1
            else:
                raise GeminiQuotaExceeded("Quota exceeded")
        mock_generate_blog.side_effect = generate_blog_side_effect
        
        # Run
        result = run_pipeline()
        
        # Verify
        mock_fetch_latest_news.assert_called_once_with(limit=3)
        self.assertEqual(mock_generate_blog.call_count, 2)
        self.assertEqual(mock_generate_image.call_count, 1)
        mock_notify.assert_called_once_with(
            reason="gemini_quota_exceeded",
            processed_count=1,
            total_attempted=4
        )
        
        self.assertEqual(result['fetched'], 3)
        self.assertEqual(result['scraped'], 4)
        self.assertEqual(result['blogs'], 1)
        self.assertEqual(result['images'], 1)
        self.assertTrue(result['quota_exceeded'])
        
        # 3 scraped items should be carried_over in DB, plus the 2 original carried over
        carried_over_db = RawNewsItem.objects.filter(status='carried_over')
        self.assertEqual(carried_over_db.count(), 5)
        self.assertEqual(RawNewsItem.objects.filter(status='carried_over', title__startswith='Scraped').count(), 3)

    @patch('pipeline.orchestrator.send_mail')
    def test_send_failure_notification(self, mock_send_mail):
        from pipeline.orchestrator import send_failure_notification
        
        with patch('pipeline.orchestrator.config') as mock_config:
            def config_side_effect(key, default=None):
                if key == 'ADMIN_NOTIFICATION_EMAIL':
                    return 'admin@example.com'
                if key == 'EMAIL_HOST_USER':
                    return 'alerts@example.com'
                return default
            mock_config.side_effect = config_side_effect
            
            SystemNotification.objects.all().delete()
            
            send_failure_notification(reason="gemini_quota_exceeded", processed_count=2, total_attempted=5)
            
            notifications = SystemNotification.objects.filter(is_resolved=False)
            self.assertEqual(notifications.count(), 1)
            notification = notifications.first()
            self.assertIn("Daily pipeline paused: Gemini API quota exceeded after generating 2 of 5 blogs.", notification.message)
            
            mock_send_mail.assert_called_once_with(
                subject="Daily News Pipeline Alert: Quota Exceeded",
                message=notification.message,
                from_email="alerts@example.com",
                recipient_list=["admin@example.com"],
                fail_silently=False
            )

    @patch('pipeline.orchestrator.send_mail')
    def test_send_failure_notification_email_error_graceful(self, mock_send_mail):
        from pipeline.orchestrator import send_failure_notification
        
        mock_send_mail.side_effect = Exception("SMTP Connection Timeout")
        
        with patch('pipeline.orchestrator.config') as mock_config:
            def config_side_effect(key, default=None):
                if key == 'ADMIN_NOTIFICATION_EMAIL':
                    return 'admin@example.com'
                return default
            mock_config.side_effect = config_side_effect
            
            SystemNotification.objects.all().delete()
            
            # This should not crash the execution
            send_failure_notification(reason="gemini_quota_exceeded", processed_count=2, total_attempted=5)
            
            self.assertEqual(SystemNotification.objects.filter(is_resolved=False).count(), 1)




