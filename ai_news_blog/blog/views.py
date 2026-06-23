from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from .models import BlogPost

def post_list(request):
    """
    Lists published blog posts ordered by newest first, 10 per page.
    """
    posts = BlogPost.objects.filter(status='published').order_by('-published_at')
    paginator = Paginator(posts, 10)
    
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'blog/post_list.html', {'page_obj': page_obj})

def post_detail(request, slug):
    """
    Details page for a single published blog post.
    """
    post = get_object_or_404(BlogPost, slug=slug, status='published')
    return render(request, 'blog/post_detail.html', {'post': post})
