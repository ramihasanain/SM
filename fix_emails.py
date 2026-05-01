import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from api_app.models import CustomUser

seen = set()
for user in CustomUser.objects.all():
    if not user.email:
        continue
    if user.email in seen:
        user.email = f"dup_{user.id}_{user.email}"
        user.save()
    else:
        seen.add(user.email)

print("Duplicate emails resolved.")
