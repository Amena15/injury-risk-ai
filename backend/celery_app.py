import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from celery import Celery

celery = Celery(
    'injury_ai',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0',
    include=['tasks']
)

celery.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,
    result_expires=3600,
)