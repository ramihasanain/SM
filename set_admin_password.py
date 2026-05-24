import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from api_app.models import CustomUser

def run():
    # Try to find user 'admin'
    user, created = CustomUser.objects.get_or_create(
        username='admin',
        defaults={
            'email': 'admin@example.com',
            'is_staff': True,
            'is_superuser': True
        }
    )
    
    # Set complex password that satisfies all requirements
    user.set_password('University@2026')
    user.is_staff = True
    user.is_superuser = True
    user.save()
    
    print("=========================================")
    if created:
        print("Successfully created user: admin")
    else:
        print("Successfully updated existing user: admin")
    print("Password set to: University@2026")
    print("is_staff:", user.is_staff)
    print("is_superuser:", user.is_superuser)
    print("=========================================")

if __name__ == '__main__':
    run()
