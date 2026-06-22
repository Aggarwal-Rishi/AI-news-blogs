from django.contrib import admin
from .models import RawNewsItem

@admin.register(RawNewsItem)
class RawNewsItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'fetched_at')
    list_filter = ('status', 'fetched_at')
    search_fields = ('title', 'scraped_content')
