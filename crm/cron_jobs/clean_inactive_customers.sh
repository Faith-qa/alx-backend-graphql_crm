#!/bin/bash

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"

# Change to the project directory
cd "$PROJECT_DIR"

# Set Python path to include the project directory
export PYTHONPATH="${PROJECT_DIR}:${PYTHONPATH}"

# If in test mode, use a fixed date
if [ "$TEST_MODE" = "1" ]; then
    DJANGO_SETTINGS_MODULE=alx_backend_graphql.settings python manage.py cleanup_inactive_customers --reference-date="2024-01-01"
else
    # Execute the cleanup command using Django's management command
    DJANGO_SETTINGS_MODULE=alx_backend_graphql.settings python manage.py cleanup_inactive_customers
fi 