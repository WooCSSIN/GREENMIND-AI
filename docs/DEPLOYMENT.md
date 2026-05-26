# GreenMind Production Deployment Guide

Follow these steps to deploy GreenMind to a production environment.

## Prerequisites

- SQL Server 2017+ (with TCP/IP enabled).
- Python 3.10+
- IIS or Nginx (as Reverse Proxy).

## Step 1: Environment Setup

1. Clone the repository.
2. Create a virtual environment: `python -m venv venv`
3. Install dependencies: `pip install -r requirements.txt`
4. Create `.env.production` (see `.env.example` for template).

## Step 2: Database Initialization

1. Execute `database/Create_table.sql` on your production SQL instance.
2. Execute `database/migration_v3_security.sql` to apply security constraints.
3. Execute `database/TRASACTION.sql` to setup stored procedures.
4. Execute `database/TRIGGERS.sql` for CO2 logic.

## Step 3: Application Configuration

1. Set environment variables:
   ```bash
   export DJANGO_SETTINGS_MODULE=greenmind_web.settings
   export DEBUG=False
   export SECRET_KEY=your-secure-key
   export ALLOWED_HOSTS=yourdomain.com
   ```
2. Collect static files: `python manage.py collectstatic`

## Step 4: Serving the Application

### Using Gunicorn (Linux)

```bash
gunicorn greenmind_web.wsgi:application --bind 0.0.0.0:8000
```

### Using Waitress/IIS (Windows)

We recommend using **Waitress** for Python serving on Windows:

```bash
waitress-serve --port=8000 greenmind_web.wsgi:application
```

Then configure IIS as a Reverse Proxy to point to localhost:8000.

## Step 5: Post-Deployment Check

Run the built-in system check:

```bash
python manage.py check --deploy
```

Check the output for any remaining security warnings.
