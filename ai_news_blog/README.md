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


## Production Deployment Guide (Render)

This application is configured for deployment to **Render** (using Gunicorn as the WSGI server and WhiteNoise to serve static files).

### 1. Database Setup (PostgreSQL)
To run in production, the application requires a PostgreSQL database. You can host this directly on Render or use a dedicated database host:
- **Render PostgreSQL (Free Trial)**: In your Render dashboard, click **New > PostgreSQL**. Follow the prompts to create a database. Note that Render's free tier databases expire 90 days after creation.
- **Neon / Aiven (Permanent Free Tiers)**: Alternatively, you can create a free PostgreSQL database on [Neon](https://neon.tech/) or [Aiven](https://aiven.io/) which do not have a 90-day expiration limit.
- Once created, copy the **External Database URL** (connection string starting with `postgres://` or `postgresql://`).

### 2. Create the Web Service on Render
1. Connect your GitHub account to Render.
2. Click **New > Web Service** and select this repository.
3. Configure the service settings:
   - **Name**: `ai-news-blog`
   - **Environment**: `Python`
   - **Build Command**: `pip install -r requirements.txt && python manage.py collectstatic --noinput`
   - **Start Command**: `gunicorn ai_news_blog.wsgi --log-file -`
   - **Instance Type**: `Free`

### 3. Configure Environment Variables
In your Web Service's dashboard, navigate to the **Environment** tab and add the following environment variables:
- `DJANGO_SECRET_KEY`: A secure random secret key.
- `DATABASE_URL`: The PostgreSQL connection string obtained in Step 1.
- `ALLOWED_HOSTS`: Your Render service URL (e.g. `your-app-name.onrender.com`).
- `DEBUG`: `False`
- `GEMINI_API_KEY`: API key for Gemini content writing.
- `ADMIN_NOTIFICATION_EMAIL`: Target email address for quota-exceeded alerts.
- `EMAIL_HOST`: SMTP server host.
- `EMAIL_PORT`: SMTP server port.
- `EMAIL_HOST_USER`: Authenticated email username.
- `EMAIL_HOST_PASSWORD`: Authenticated email password.
- `EMAIL_USE_TLS`: `True` or `False`.

### 4. Run Migrations & Create Publisher Account
Once the service has finished its initial build and deployed:
1. Navigate to the **Shell** (or Console) tab in the Render dashboard for your Web Service.
2. Run database migrations:
   ```bash
   python manage.py migrate
   ```
3. Create the initial Publisher admin user:
   ```bash
   python manage.py createsuperuser
   ```
   Follow the prompts to enter a username, email, and password. This account will be used to log in to the admin dashboard.

### 5. Post-Deployment Verification
After completing the setup:
- **Public Blog**: Navigate to `https://your-app-name.onrender.com/` to verify that the home page loads successfully with all static assets (CSS and images) displaying correctly.
- **Publisher Dashboard**: Navigate to `https://your-app-name.onrender.com/dashboard/login/` and log in using the credentials created in Step 4 to verify the admin workstations are reachable and fully functioning.


