from django.test import TestCase
from unittest.mock import patch, MagicMock
from blog.models import BlogPost
from .news_fetcher import fetch_latest_news
from .models import RawNewsItem
from .image_generator import build_image_prompt, generate_image, regenerate_image

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

