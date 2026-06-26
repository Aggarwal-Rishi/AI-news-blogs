import logging
import requests
import urllib.parse
from google import genai
from decouple import config

logger = logging.getLogger(__name__)

# Configure Gemini client
api_key = config('GEMINI_API_KEY', default=None)
if api_key:
    client = genai.Client(api_key=api_key)
else:
    client = None
    logger.warning("GEMINI_API_KEY not found.")

MODEL = 'gemini-3.5-flash'

def build_image_prompt(blog_post):
    """
    Constructs a visual scene description for image generation using Gemini.
    """
    if not client:
        return f"A futuristic digital illustration representing {blog_post.title}"

    prompt = f"""
    Based on the following blog post title and intro, create a short (15-20 words),
    highly descriptive visual prompt for an AI image generator.
    
    RULES:
    - Describe a visual scene (lighting, objects, mood, style).
    - Do NOT include any text or words in the image.
    - Style: Professional, high-tech, futuristic, photorealistic.
    - Output ONLY the final prompt string, nothing else.
    
    TITLE: {blog_post.title}
    EXCERPT: {blog_post.excerpt}
    """

    try:
        response = client.models.generate_content(model=MODEL, contents=prompt)
        return response.text.strip()
    except Exception as e:
        logger.error(f"Failed to build image prompt via Gemini: {e}")
        return f"A futuristic digital illustration representing {blog_post.title}"

def generate_image(blog_post, is_retry=False):
    """
    Generates a featured image URL using Pollinations.ai and saves it to the blog post.
    """
    if is_retry:
        prompt_text = f"Abstract high-tech futuristic background, cinematic lighting, 4k digital art"
    else:
        prompt_text = build_image_prompt(blog_post)

    logger.info(f"Generating image for post {blog_post.id} with prompt: {prompt_text}")

    encoded_prompt = urllib.parse.quote(prompt_text)
    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=576&nologo=true&seed=42"

    try:
        response = requests.get(image_url, timeout=15)

        if response.status_code == 200 and 'image' in response.headers.get('Content-Type', ''):
            blog_post.featured_image_url = image_url
            blog_post.save()
            logger.info(f"Successfully generated image for post {blog_post.id}")
            return True
        else:
            logger.warning(f"Pollinations returned invalid response (Status: {response.status_code})")
            if not is_retry:
                return generate_image(blog_post, is_retry=True)
            return False

    except (requests.RequestException, Exception) as e:
        logger.error(f"Error calling Pollinations.ai for post {blog_post.id}: {e}")
        if not is_retry:
            logger.info("Retrying with simplified prompt...")
            return generate_image(blog_post, is_retry=True)
        logger.error("Image generation failed after retry. Leaving featured_image_url blank.")
        return False

def regenerate_image(blog_post):
    """
    Explicitly re-runs image generation for an existing post.
    """
    return generate_image(blog_post)
