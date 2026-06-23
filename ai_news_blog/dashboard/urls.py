from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('login/', views.dashboard_login, name='login'),
    path('logout/', views.dashboard_logout, name='logout'),
    path('', views.dashboard_index, name='index'),
    path('post/<int:post_id>/', views.post_detail, name='post_detail'),
    path('post/<int:post_id>/publish/', views.post_publish, name='post_publish'),
    path('post/<int:post_id>/reject/', views.post_reject, name='post_reject'),
    path('post/<int:post_id>/regenerate-text/', views.post_regenerate_text, name='post_regenerate_text'),
    path('post/<int:post_id>/regenerate-image/', views.post_regenerate_image, name='post_regenerate_image'),
    path('published/', views.published_list, name='published_list'),
    path('notification/<int:notification_id>/dismiss/', views.notification_dismiss, name='notification_dismiss'),

]
