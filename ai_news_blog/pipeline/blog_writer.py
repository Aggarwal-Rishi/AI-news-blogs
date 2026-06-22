import json
import logging
import google.generativeai as genai
from django.utils import timezone
from decouple import config
from blog.models import BlogPost
from .models import RawNewsItem

logger = logging.getLogger(__name__)

# Custom exception for quota issues
class GeminiQuotaExceeded(Exception):
    pass

# Configure Gemini
api_key = config('GEMINI_API_KEY', default=None)
if api_key:
    genai.configure(api_key=api_key)
else:
    logger.warning("GEMINI_API_KEY not found in environment settings.")

def _get_gemini_response(prompt, retry=True):
    """
    Helper to call Gemini and handle JSON parsing.
    """
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        
        # Strip markdown code fences if present
        if text.startswith('```'):
            lines = text.splitlines()
            if lines[0].startswith('```json'):
                text = '\n'.join(lines[1:-1])
            else:
                text = '\n'.join(lines[1:-1])

        return json.loads(text)
    except json.JSONDecodeError as e:
        if retry:
            logger.warning("JSON parsing failed, retrying once with stricter prompt.")
            stricter_prompt = prompt + "\n\nIMPORTANT: Return ONLY valid JSON. Do not include markdown code blocks or any other text."
            return _get_gemini_response(stricter_prompt, retry=False)
        else:
            logger.error(f"Failed to parse JSON from Gemini after retry: {e}")
            raise
    except Exception as e:
        # Check if it's a quota error (status code 429)
        if hasattr(e, 'status_code') and e.status_code == 429:
            raise GeminiQuotaExceeded("Gemini API quota exceeded.")
        # Some SDK versions might wrap it differently
        if "429" in str(e) or "quota" in str(e).lower():
            raise GeminiQuotaExceeded("Gemini API quota exceeded.")
        
        logger.error(f"Error calling Gemini API: {e}")
        raise

def generate_blog(raw_news_item):
    """
    Generates a blog post from a RawNewsItem using Gemini.
    """
    if not raw_news_item.scraped_content:
        logger.error(f"RawNewsItem {raw_news_item.id} has no scraped content.")
        return None

    prompt = f"""
    You are a professional tech blogger. Rewrite the following news article into a structured blog post.
    
    RULES:
    1. Rewrite fully in your own words. No close paraphrasing or copying sentences.
    2. TOTAL WORD COUNT: Between 400 and 600 words.
    3. TEMPLATE:
       - A catchy but accurate title.
       - A 1-2 sentence intro/hook.
       - 2-3 body sections with subheadings.
       - A 1-2 sentence conclusion/takeaway.
    4. NO SOURCE MENTION: Do not mention the original source, outlet, or link back to it.
    5. OUTPUT FORMAT: Return ONLY valid JSON with these keys:
       "title": "...",
       "intro": "...",
       "sections": [{"subheading": "...", "content": "..."}],
       "conclusion": "...",
       "excerpt": "..." (a short summary for a list page)

    SOURCE ARTICLE:
    {raw_news_item.scraped_content}
    """

    try:
        data = _get_gemini_response(prompt)
        
        # Combine content into HTML/Markdown
        content_parts = [f"<p>{data['intro']}</p>"]
        for section in data['sections']:
            content_parts.append(f"<h2>{section['subheading']}</h2>")
            content_parts.append(f"<p>{section['content']}</p>")
        content_parts.append(f"<p><strong>Conclusion:</strong> {data['conclusion']}</p>")
        
        full_content = "\n\n".join(content_parts)

        # Create BlogPost
        blog_post = BlogPost.objects.create(
            title=data['title'],
            content=full_content,
            excerpt=data['excerpt'],
            status='pending',
            pending_since=timezone.now(),
            source_url=raw_news_item.resolved_article_url or raw_news_item.google_news_link,
            source_news_title=raw_news_item.title
        )

        # Link and update RawNewsItem
        raw_news_item.linked_blog_post = blog_post
        raw_news_item.status = 'written'
        raw_news_item.save()

        return blog_post

    except GeminiQuotaExceeded:
        logger.warning(f"Quota exceeded while processing item {raw_news_item.id}")
        raise
    except Exception as e:
        logger.error(f"Failed to generate blog for item {raw_news_item.id}: {e}")
        return None

def regenerate_blog_content(blog_post):
    """
    Regenerates the content of an existing BlogPost using the linked RawNewsItem.
    """
    raw_news_item = getattr(blog_post, 'raw_news_item_set', None)
    # If not found directly, try reverse relation or through the field in RawNewsItem
    if not raw_news_item:
        raw_news_item = RawNewsItem.objects.filter(linked_blog_post=blog_post).first()

    if not raw_news_item or not raw_news_item.scraped_content:
        logger.error(f"Cannot regenerate: No linked scraped content for BlogPost {blog_post.id}")
        return False

    prompt = f"""
    You are a professional tech blogger. REGENERATE this blog post to be better and fresher.
    
    RULES: [SAME AS BEFORE]
    - Word count: 400-600 words.
    - Template: title, intro, 2-3 sections, conclusion.
    - NO source mentions.
    - Format: JSON.

    SOURCE ARTICLE:
    {raw_news_item.scraped_content}
    """

    try:
        data = _get_gemini_response(prompt)
        
        content_parts = [f"<p>{data['intro']}</p>"]
        for section in data['sections']:
            content_parts.append(f"<h2>{section['subheading']}</h2>")
            content_parts.append(f"<p>{section['content']}</p>")
        content_parts.append(f"<p><strong>Conclusion:</strong> {data['conclusion']}</p>")
        
        full_content = "\n\n".join(content_parts)

        # Update BlogPost
        blog_post.title = data['title']
        blog_post.content = full_content
        blog_post.excerpt = data['excerpt']
        
        if blog_post.status == 'pending':
            blog_post.pending_since = timezone.now()
            
        blog_post.save()
        return True

    except Exception as e:
        logger.error(f"Failed to regenerate blog for post {blog_post.id}: {e}")
        return False
