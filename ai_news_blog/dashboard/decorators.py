from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from functools import wraps

def dashboard_member_required(view_func):
    """
    Decorator that checks if a user is logged in and has a Profile with an editor or publisher role.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('dashboard:login')
        
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)
            
        try:
            profile = request.user.profile
            if profile.role in ['editor', 'publisher']:
                return view_func(request, *args, **kwargs)
        except AttributeError:
            pass
            
        raise PermissionDenied("You must be a dashboard member with editor or publisher role to access this page.")
    return _wrapped_view

def publisher_required(view_func):
    """
    Decorator that checks if a user is logged in and has a Profile with a publisher role.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('dashboard:login')
            
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)

        try:
            profile = request.user.profile
            if profile.role == 'publisher':
                return view_func(request, *args, **kwargs)
        except AttributeError:
            pass
            
        raise PermissionDenied("Only publishers are authorized to perform this action.")
    return _wrapped_view
