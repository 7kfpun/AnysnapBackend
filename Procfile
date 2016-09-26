web: gunicorn backend.wsgi --log-file -
worker: python manage.py celery worker --loglevel=info
