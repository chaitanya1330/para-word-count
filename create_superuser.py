import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'para_word_count.settings')
django.setup()

from django.contrib.auth.models import User

if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@test.com', 'admin123')
    print('Superuser created successfully')
else:
    print('Superuser already exists')
