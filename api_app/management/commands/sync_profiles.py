from django.core.management.base import BaseCommand
from api_app.models import SocialProfile
from api_app.social_sync import fetch_facebook_posts

class Command(BaseCommand):
    help = 'Syncs posts for all connected social profiles using their OAuth tokens'

    def handle(self, *args, **kwargs):
        profiles = SocialProfile.objects.exclude(access_token__isnull=True).exclude(access_token='')
        
        self.stdout.write(self.style.SUCCESS(f"Found {profiles.count()} active profiles to sync..."))
        
        for profile in profiles:
            self.stdout.write(f"Syncing profile ID: {profile.id} ({profile.platform}) - Account: {profile.platform_account_id}")
            
            if profile.platform == 'facebook':
                try:
                    fetch_facebook_posts(profile.id)
                    self.stdout.write(self.style.SUCCESS(f"Finished syncing profile {profile.id}"))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Failed to sync profile {profile.id}: {str(e)}"))
                    
            elif profile.platform == 'twitter':
                self.stdout.write(self.style.WARNING("X (Twitter) sync function is not implemented yet."))
        
        self.stdout.write(self.style.SUCCESS('Done!'))
