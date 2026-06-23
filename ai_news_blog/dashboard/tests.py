import datetime
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from unittest.mock import patch

from blog.models import BlogPost
from dashboard.models import Profile, SystemNotification

class DashboardAccessTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.editor_user = User.objects.create_user(username='editor', password='password123')
        self.editor_profile = Profile.objects.create(user=self.editor_user, role='editor')
        
        self.publisher_user = User.objects.create_user(username='publisher', password='password123')
        self.publisher_profile = Profile.objects.create(user=self.publisher_user, role='publisher')
        
        self.regular_user = User.objects.create_user(username='regular', password='password123')
        
        self.post = BlogPost.objects.create(
            title="Test Title",
            content="<p>Test content</p>",
            excerpt="Test excerpt",
            status="pending",
            pending_since=timezone.now(),
            source_url="http://example.com",
            source_news_title="Source News"
        )

    def test_anonymous_redirect(self):
        response = self.client.get(reverse('dashboard:index'))
        self.assertRedirects(response, reverse('dashboard:login'))

    def test_regular_user_denied(self):
        self.client.login(username='regular', password='password123')
        response = self.client.get(reverse('dashboard:index'))
        self.assertEqual(response.status_code, 403)

    def test_editor_access(self):
        self.client.login(username='editor', password='password123')
        
        response = self.client.get(reverse('dashboard:index'))
        self.assertEqual(response.status_code, 200)
        
        response = self.client.get(reverse('dashboard:post_detail', args=[self.post.id]))
        self.assertEqual(response.status_code, 200)

        response = self.client.post(reverse('dashboard:post_publish', args=[self.post.id]))
        self.assertEqual(response.status_code, 403)

    def test_publisher_access(self):
        self.client.login(username='publisher', password='password123')
        
        response = self.client.get(reverse('dashboard:index'))
        self.assertEqual(response.status_code, 200)
        
        response = self.client.post(reverse('dashboard:post_publish', args=[self.post.id]))
        self.assertRedirects(response, reverse('dashboard:index'))
        
        self.post.refresh_from_db()
        self.assertEqual(self.post.status, 'published')
        self.assertIsNotNone(self.post.published_at)

class DashboardActionsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.publisher_user = User.objects.create_user(username='publisher', password='password123')
        self.publisher_profile = Profile.objects.create(user=self.publisher_user, role='publisher')
        self.client.login(username='publisher', password='password123')
        
        self.post = BlogPost.objects.create(
            title="Test Title",
            content="<p>Test content</p>",
            excerpt="Test excerpt",
            status="pending",
            pending_since=timezone.now(),
            source_url="http://example.com",
            source_news_title="Source News"
        )

    def test_post_detail_edit(self):
        data = {
            'title': 'New Updated Title',
            'excerpt': 'New excerpt details',
            'content': '<p>New content body</p>'
        }
        response = self.client.post(reverse('dashboard:post_detail', args=[self.post.id]), data)
        self.assertRedirects(response, reverse('dashboard:post_detail', args=[self.post.id]))
        
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, 'New Updated Title')
        self.assertEqual(self.post.excerpt, 'New excerpt details')
        self.assertEqual(self.post.content, '<p>New content body</p>')

    def test_post_reject(self):
        response = self.client.post(reverse('dashboard:post_reject', args=[self.post.id]))
        self.assertRedirects(response, reverse('dashboard:index'))
        
        self.post.refresh_from_db()
        self.assertEqual(self.post.status, 'rejected')

    @patch('dashboard.views.regenerate_blog_content')
    def test_post_regenerate_text(self, mock_regen_text):
        mock_regen_text.return_value = True
        response = self.client.post(reverse('dashboard:post_regenerate_text', args=[self.post.id]))
        self.assertRedirects(response, reverse('dashboard:post_detail', args=[self.post.id]))
        mock_regen_text.assert_called_once_with(self.post)

    @patch('dashboard.views.regenerate_image')
    def test_post_regenerate_image(self, mock_regen_image):
        mock_regen_image.return_value = True
        response = self.client.post(reverse('dashboard:post_regenerate_image', args=[self.post.id]))
        self.assertRedirects(response, reverse('dashboard:post_detail', args=[self.post.id]))
        mock_regen_image.assert_called_once_with(self.post)

class DashboardViewLogicTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.editor_user = User.objects.create_user(username='editor', password='password123')
        self.editor_profile = Profile.objects.create(user=self.editor_user, role='editor')
        self.client.login(username='editor', password='password123')

    def test_deadline_calculations(self):
        now = timezone.now()
        p1 = BlogPost.objects.create(
            title="Post 1", content="c", excerpt="e", status="pending",
            pending_since=now - datetime.timedelta(hours=10),
            source_url="http://1", source_news_title="s1"
        )
        p2 = BlogPost.objects.create(
            title="Post 2", content="c", excerpt="e", status="pending",
            pending_since=now - datetime.timedelta(hours=50),
            source_url="http://2", source_news_title="s2"
        )
        
        response = self.client.get(reverse('dashboard:index'))
        posts_in_context = response.context['posts']
        
        p1_retrieved = next(p for p in posts_in_context if p.id == p1.id)
        p2_retrieved = next(p for p in posts_in_context if p.id == p2.id)
        
        self.assertIn("37h", p1_retrieved.time_remaining)
        self.assertEqual(p2_retrieved.time_remaining, "Overdue")

    def test_notifications_banner(self):
        unresolved = SystemNotification.objects.create(message="System failure", is_resolved=False)
        resolved = SystemNotification.objects.create(message="Database backup failed", is_resolved=True)
        
        response = self.client.get(reverse('dashboard:index'))
        notifications_in_context = response.context['notifications']
        
        self.assertIn(unresolved, notifications_in_context)
        self.assertNotIn(resolved, notifications_in_context)
