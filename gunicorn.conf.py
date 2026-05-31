import os

# Render dynamically sets the PORT environment variable.
port = os.environ.get('PORT', '10000')
bind = f"0.0.0.0:{port}"

# Use 1 worker but multiple threads to handle concurrent requests without using too much RAM
workers = 1
threads = 4

# CRITICAL: AI requests take a long time! Gunicorn's default timeout is 30s. 
# We increase it to 5 minutes (300s) so the AI has time to think and write code.
timeout = 300

# Log to stdout so it shows up in the Render dashboard
accesslog = '-'
errorlog = '-'
