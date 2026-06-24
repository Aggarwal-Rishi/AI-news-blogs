import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.utils import timezone

from blog.models import BlogPost
from dashboard.models import SystemNotification
from dashboard.decorators import dashboard_member_required, publisher_required
from dashboard.forms import BlogPostForm
from pipeline.blog_writer import regenerate_blog_content
from pipeline.image_generator import regenerate_image

def dashboard_login(request):
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect('dashboard:index')
        try:
            if request.user.profile.role in ['editor', 'publisher']:
                return redirect('dashboard:index')
        except AttributeError:
            pass

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if user.is_superuser:
                auth_login(request, user)
                return redirect('dashboard:index')
            try:
                profile = user.profile
                if profile.role in ['editor', 'publisher']:
                    auth_login(request, user)
                    return redirect('dashboard:index')
                else:
                    messages.error(request, "Access restricted: You do not have editor or publisher permissions.")
            except AttributeError:
                messages.error(request, "Access restricted: No user profile associated.")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    return render(request, 'dashboard/login.html', {'form': form})

def dashboard_logout(request):
    auth_logout(request)
    return redirect('dashboard:login')

@dashboard_member_required
def dashboard_index(request):
    pending_posts = BlogPost.objects.filter(status='pending').order_by('pending_since')
    
    # Calculate time remaining for 48-hour auto-publish deadline
    for post in pending_posts:
        if post.pending_since:
            deadline = post.pending_since + datetime.timedelta(hours=48)
            now = timezone.now()
            if deadline > now:
                diff = deadline - now
                total_seconds = int(diff.total_seconds())
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                post.time_remaining = f"{hours}h {minutes}m"
            else:
                post.time_remaining = "Overdue"
        else:
            post.time_remaining = "No deadline"
            
    notifications = SystemNotification.objects.filter(is_resolved=False).order_by('-created_at')
    
    context = {
        'posts': pending_posts,
        'notifications': notifications
    }
    return render(request, 'dashboard/index.html', context)

@dashboard_member_required
def post_detail(request, post_id):
    post = get_object_or_404(BlogPost, id=post_id)
    
    if request.method == 'POST':
        form = BlogPostForm(request.POST, instance=post)
        if form.is_valid():
            form.save()
            messages.success(request, "Post updated successfully.")
            return redirect('dashboard:post_detail', post_id=post.id)
    else:
        form = BlogPostForm(instance=post)
        
    context = {
        'post': post,
        'form': form
    }
    return render(request, 'dashboard/post_detail.html', context)

@publisher_required
@require_POST
def post_publish(request, post_id):
    post = get_object_or_404(BlogPost, id=post_id)
    post.status = 'published'
    post.published_at = timezone.now()
    post.save()
    messages.success(request, f"Post '{post.title}' published successfully.")
    return redirect('dashboard:index')

@dashboard_member_required
@require_POST
def post_reject(request, post_id):
    post = get_object_or_404(BlogPost, id=post_id)
    post.status = 'rejected'
    post.save()
    messages.success(request, f"Post '{post.title}' marked as rejected.")
    return redirect('dashboard:index')

@dashboard_member_required
@require_POST
def post_regenerate_text(request, post_id):
    post = get_object_or_404(BlogPost, id=post_id)
    success = regenerate_blog_content(post)
    if success:
        messages.success(request, "Blog text successfully regenerated using Gemini.")
    else:
        messages.error(request, "Failed to regenerate blog text.")
    return redirect('dashboard:post_detail', post_id=post.id)

@dashboard_member_required
@require_POST
def post_regenerate_image(request, post_id):
    post = get_object_or_404(BlogPost, id=post_id)
    success = regenerate_image(post)
    if success:
        messages.success(request, "Featured image successfully regenerated.")
    else:
        messages.error(request, "Failed to regenerate featured image.")
    return redirect('dashboard:post_detail', post_id=post.id)

@dashboard_member_required
def published_list(request):
    published_posts = BlogPost.objects.filter(status='published').order_by('-published_at')
    return render(request, 'dashboard/published.html', {'posts': published_posts})

@dashboard_member_required
@require_POST
def notification_dismiss(request, notification_id):
    notification = get_object_or_404(SystemNotification, id=notification_id)
    notification.is_resolved = True
    notification.save()
    messages.success(request, "Notification marked as resolved.")
    return redirect('dashboard:index')

