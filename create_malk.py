import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eliterent_gateway.settings')
django.setup()

from django.contrib.auth.models import User
from auth_service.models import Profile

def create_user(username, email, password, role='client'):
    if not User.objects.filter(username=username).exists():
        user = User.objects.create_superuser(username=username, email=email, password=password)
        profile, created = Profile.objects.get_or_create(user=user)
        profile.role = role
        profile.save()
        print(f"User '{username}' created successfully.")
    else:
        print(f"User '{username}' already exists.")

create_user('malk', 'malk@test.com', 'malk123', 'admin')
