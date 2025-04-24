# CRM System with Celery Weekly Reports

This CRM system includes a weekly report generation feature using Celery and Celery Beat.

## Setup Instructions

1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run Django migrations:
   ```bash
   python manage.py migrate
   ```

3. Start the Celery worker:
   ```bash
   celery -A crm worker -l info
   ```

4. Start Celery Beat:
   ```bash
   celery -A crm beat -l info
   ```

## Weekly Report Generation

- Reports are generated every Monday at 6:00 AM
- Reports are logged to `/tmp/crm_report_log.txt`
- Each report includes:
  - Total number of customers
  - Total number of orders
  - Total revenue

## Log File Format

The log file (`/tmp/crm_report_log.txt`) will contain entries in the following format:
```
YYYY-MM-DD HH:MM:SS - Report: X customers, Y orders, $Z.ZZ revenue
```

## Troubleshooting

1. If Celery worker fails to start:
   - Ensure all dependencies are installed
   - Verify Django settings are correct
   - Check the Celery logs for errors

2. If reports are not being generated:
   - Check Celery Beat is running
   - Verify the schedule in settings.py
   - Check the log file for error messages

3. If GraphQL queries fail:
   - Ensure the Django server is running
   - Verify the GraphQL endpoint is accessible
   - Check the GraphQL schema for any changes 