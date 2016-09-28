export $(cat .env | xargs) && gunicorn backend.wsgi --log-file -
export $(cat .env | xargs) && python manage.py celery worker --loglevel=info

