import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'para_word_count.settings')

app = Celery('para_word_count')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

# Celery configuration for production
if __name__ == '__main__':
    app.start()
