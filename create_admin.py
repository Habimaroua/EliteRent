import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eliterent_gateway.settings')
django.setup()

from django.contrib.auth.models import User
from auth_service.models import Profile

username = 'admin'
email = 'admin@eliterent.com'
password = 'admin123'

if not User.objects.filter(username=username).exists():
    user = User.objects.create_superuser(username=username, email=email, password=password)
    profile, created = Profile.objects.get_or_create(user=user)
    profile.role = 'admin'
    profile.save()
    print(f"Superuser '{username}' created successfully (Password: {password})")
else:
    user = User.objects.get(username=username)
    user.set_password(password)
    user.save()
    profile, created = Profile.objects.get_or_create(user=user)
    profile.role = 'admin'
    profile.save()
    print(f"User '{username}' already exists. Password and Admin role updated.")
