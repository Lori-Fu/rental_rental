from celery import Celery
from rental_root.tasks import config

celery_app = Celery("rental")
celery_app.config_from_object(config)

celery_app.autodiscover_tasks(["rental_root.tasks.email"])
