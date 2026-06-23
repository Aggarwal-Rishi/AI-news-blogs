from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from .models import BlogPost

class PublicBlogViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        
        # Create published posts
        self.published_posts = []
        for i in range(15):
            post = BlogPost.objects.create(
                title=f"Published Post {i}",
                content=f"<p>Content {i}</p>",
                excerpt=f"Excerpt {i}",
                status="published",
                published_at=timezone.now() - timezone.timedelta(days=i),
                source_url=f"http://example.com/source/{i}",
                source_news_title=f"Source Title {i}"
            )
            self.published_posts.append(post)
            
        # Create pending post
        self.pending_post = BlogPost.objects.create(
            title="Pending Post",
            content="<p>Pending content</p>",
            excerpt="Pending excerpt",
            status="pending",
            source_url="http://example.com/source/pending",
            source_news_title="Source Title Pending"
        )
        
        # Create rejected post
        self.rejected_post = BlogPost.objects.create(
            title="Rejected Post",
            content="<p>Rejected content</p>",
            excerpt="Rejected excerpt",
            status="rejected",
            source_url="http://example.com/source/rejected",
            source_news_title="Source Title Rejected"
        )

    def test_homepage_post_list(self):
        response = self.client.get(reverse('blog:post_list'))
        self.assertEqual(response.status_code, 200)
        
        posts_in_context = response.context['page_obj']
        self.assertEqual(len(posts_in_context), 10)
        
        titles = [p.title for p in posts_in_context]
        self.assertNotIn("Pending Post", titles)
        self.assertNotIn("Rejected Post", titles)
        
        self.assertEqual(posts_in_context[0].title, "Published Post 0")
        self.assertEqual(posts_in_context[9].title, "Published Post 9")

    def test_homepage_pagination(self):
        response = self.client.get(reverse('blog:post_list') + '?page=2')
        self.assertEqual(response.status_code, 200)
        
        posts_in_context = response.context['page_obj']
        self.assertEqual(len(posts_in_context), 5)
        self.assertEqual(posts_in_context[0].title, "Published Post 10")
        self.assertEqual(posts_in_context[4].title, "Published Post 14")

    def test_post_detail_success(self):
        post = self.published_posts[0]
        response = self.client.get(reverse('blog:post_detail', args=[post.slug]))
        self.assertEqual(response.status_code, 200)
        
        self.assertContains(response, post.title)
        self.assertContains(response, post.content)
        
        self.assertNotContains(response, post.source_url)
        self.assertNotContains(response, post.source_news_title)

    def test_post_detail_unpublished_returns_404(self):
        response = self.client.get(reverse('blog:post_detail', args=[self.pending_post.slug]))
        self.assertEqual(response.status_code, 404)
        
        response = self.client.get(reverse('blog:post_detail', args=[self.rejected_post.slug]))
        self.assertEqual(response.status_code, 404)

    def test_post_detail_invalid_slug_returns_404(self):
        response = self.client.get(reverse('blog:post_detail', args=['non-existent-slug']))
        self.assertEqual(response.status_code, 404)
