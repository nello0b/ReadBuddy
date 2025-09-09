# celery_app.py

import os
from celery import Celery
import logging

logger = logging.getLogger(__name__)

try:
    logger.info("Loaded secrets from Azure Key Vault for Celery worker")
except Exception as e:
    logger.warning(f"Failed to load secrets from Azure Key Vault: {e}")

# Redis connection URL - auto-detect Docker vs local environment
def get_redis_url():
    # Check if we're running in Docker by looking for the container environment
    if os.path.exists('/.dockerenv') or os.environ.get('RUNNING_IN_DOCKER'):
        # Running in Docker - use service name from docker-compose.yml
        return "redis://redis:6379/0"
    else:
        # Running locally - use localhost
        return "redis://localhost:6379/0"

REDIS_URL = os.getenv("REDIS_URL", get_redis_url())

celery_app = Celery(
    "readbuddy",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=[
        "app.tasks.image_extraction_result_tasks",
        "app.tasks.create_quiz_task",
        "app.tasks.summarise_articles_task",
        "app.tasks.create_glossary_task",
    ],
)

# Allow passing complex Python objects between tasks
celery_app.conf.update(
    task_serializer="pickle",
    accept_content=["pickle"],
    result_serializer="pickle",
)

# Configure task discovery
celery_app.autodiscover_tasks(['app.tasks'])
