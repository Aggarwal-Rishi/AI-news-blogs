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

## GitHub Actions Workflows

We have automated pipeline jobs using GitHub Actions.

### Configured Workflows
1. **Daily News Pipeline** (`daily_pipeline.yml`): Runs daily at 06:00 UTC. It installs dependencies, sets up headlessly-driven Playwright Chromium, and executes the complete fetching, scraping, blog writing, and image generation pipeline.
2. **Hourly Auto-Publish Checker** (`hourly_auto_publish.yml`): Runs every hour to check for and publish pending posts older than 48 hours.

### Required Secrets
To make the workflows run successfully, configure the following secrets under **Settings > Secrets and variables > Actions > Repository secrets** in your GitHub repository:
- `DJANGO_SECRET_KEY`: Production Django secret key.
- `DATABASE_URL`: PostgreSQL connection string (connects directly to your Render or Railway hosting database).
- `GEMINI_API_KEY`: API key for Gemini content writing.
- `ADMIN_NOTIFICATION_EMAIL`: Target email address to send quota-exceeded alerts to.
- `EMAIL_HOST`: SMTP email host server.
- `EMAIL_PORT`: SMTP email port.
- `EMAIL_HOST_USER`: Authenticated email user.
- `EMAIL_HOST_PASSWORD`: Authenticated email user password.
- `EMAIL_USE_TLS`: Set to `True` or `False` depending on TLS requirements.

> [!NOTE]
> Since the production database is hosted externally (e.g., Render/Railway), GitHub runners connect directly to it using the `DATABASE_URL` secret. No separate server execution is required for scheduled runs.

### Manual Execution
To manually trigger either workflow for testing:
1. Navigate to the **Actions** tab in your GitHub repository.
2. Select either **Daily News Pipeline** or **Hourly Auto-Publish Checker** from the list of workflows on the left side.
3. Click the **Run workflow** dropdown button on the right.
4. Select the target branch and click the green **Run workflow** button.

