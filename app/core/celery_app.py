from celery import Celery

from app.core.config import settings


celery_app = Celery(
    "lcms_identification",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    task_track_started=True,
    result_expires=3600,
    task_always_eager=settings.celery_task_always_eager,
    task_store_eager_result=True,
)