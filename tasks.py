import celery
import os

app = celery.Celery('example')
app.conf.update(BROKER_URL=os.environ['REDIS_URL'],
                CELERY_RESULT_BACKEND=os.environ['REDIS_URL'])


@app.task
def add(x, y):
    """Add."""
    return x + y


@app.task
def crafter_upload():
    """Update."""
    return True


@app.task
def google_vision():
    """Google vision."""
    return True


@app.task
def sync_firebase():
    """Sync firebase."""
    return True
