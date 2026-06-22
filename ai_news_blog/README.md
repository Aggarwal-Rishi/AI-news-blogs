# AI News Blog

An AI-powered news blog platform built with Django.

## Setup Instructions

### Prerequisites
- Python 3.13+
- PostgreSQL (or SQLite for local development)

### Installation
1. Clone the repository.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Install Playwright browsers:
   ```bash
   python -m playwright install chromium
   ```

### Running the Pipeline
- **Fetch News**: `python manage.py fetch_news`
- **Scrape News**: `python manage.py scrape_news`
