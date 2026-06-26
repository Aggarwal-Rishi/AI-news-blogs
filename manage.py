#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    # Change working directory to the subfolder where the actual Django project resides
    os.chdir(os.path.join(os.path.dirname(__file__), "ai_news_blog"))
    sys.path.insert(0, os.path.abspath("."))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ai_news_blog.settings")
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
