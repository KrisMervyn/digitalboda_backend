web: gunicorn --bind 0.0.0.0:$PORT digitalboda_backend.wsgi:application
worker: celery -A digitalboda_backend worker --loglevel=info
beat: celery -A digitalboda_backend beat --loglevel=info