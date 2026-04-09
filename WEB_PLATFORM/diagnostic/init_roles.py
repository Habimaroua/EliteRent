from django.contrib.auth.models import User
from inspections.models import Profile

for user in User.objects.all():
    p, created = Profile.objects.get_or_create(user=user)
    if user.is_staff:
        p.role = 'admin'
    else:
        p.role = 'client'
    p.save()
    print(f"User {user.username} - Role: {p.role}")
