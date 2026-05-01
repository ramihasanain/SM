import os
import requests
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
from urllib.parse import urlencode

from .models import SocialProfile

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def facebook_login(request):
    """Returns the Facebook OAuth authorization URL"""
    params = {
        'client_id': settings.FACEBOOK_CLIENT_ID,
        'redirect_uri': settings.FACEBOOK_REDIRECT_URI,
        'state': 'some_random_state_string',
        'scope': 'pages_show_list,pages_read_engagement,pages_read_user_content',
        'response_type': 'code'
    }
    auth_url = f"https://www.facebook.com/v19.0/dialog/oauth?{urlencode(params)}"
    return Response({'auth_url': auth_url})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def facebook_callback(request):
    """Exchanges code for access token and saves profile"""
    code = request.data.get('code')
    if not code:
        return Response({'error': 'No code provided'}, status=status.HTTP_400_BAD_REQUEST)

    token_url = "https://graph.facebook.com/v19.0/oauth/access_token"
    token_params = {
        'client_id': settings.FACEBOOK_CLIENT_ID,
        'redirect_uri': settings.FACEBOOK_REDIRECT_URI,
        'client_secret': settings.FACEBOOK_CLIENT_SECRET,
        'code': code
    }
    
    try:
        response = requests.get(token_url, params=token_params)
        data = response.json()
        
        if 'error' in data:
            error_msg = data['error'].get('message', 'Failed') if isinstance(data['error'], dict) else str(data['error'])
            # If it's a reused code due to React Strict Mode double-firing, we can just return a 400 safely
            return Response({'error': error_msg}, status=status.HTTP_400_BAD_REQUEST)
            
        access_token = data.get('access_token')
        
        accounts_url = "https://graph.facebook.com/v19.0/me/accounts"
        accounts_res = requests.get(accounts_url, params={'access_token': access_token}).json()
        pages = accounts_res.get('data', [])
        
        if not pages:
            return Response({'error': 'لا توجد صفحات فيسبوك مرتبطة بهذا الحساب'}, status=400)
            
        profile_ids = []
        for page in pages:
            page_id = page['id']
            page_token = page['access_token']
            page_name = page.get('name', 'Unknown Page')
            
            # Fetch page profile picture
            try:
                page_info_url = f"https://graph.facebook.com/v19.0/{page_id}"
                page_info_params = {'access_token': page_token, 'fields': 'picture.type(large),followers_count'}
                info_res = requests.get(page_info_url, params=page_info_params).json()
                followers = info_res.get('followers_count', 0)
                pic_url = info_res.get('picture', {}).get('data', {}).get('url', '')
            except:
                followers = 0
                pic_url = ''

            profile, created = SocialProfile.objects.update_or_create(
                user=request.user,
                platform='facebook',
                platform_account_id=page_id,
                defaults={
                    'access_token': page_token,
                    'account_name': page_name,
                    'followers_count': followers,
                    'profile_picture_url': pic_url,
                    'token_expires_at': timezone.now() + timedelta(days=60),
                }
            )
            profile_ids.append(profile.id)
        
        return Response({'message': f'تم ربط {len(profile_ids)} صفحة بنجاح', 'profile_ids': profile_ids})
        
    except Exception as e:
        import traceback
        with open('error_log.txt', 'w') as f:
            f.write(traceback.format_exc())
            f.write(f"\nData was: {locals().get('data')}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def x_login(request):
    """Returns the X (Twitter) OAuth authorization URL"""
    params = {
        'response_type': 'code',
        'client_id': settings.X_CLIENT_ID,
        'redirect_uri': settings.X_REDIRECT_URI,
        'scope': 'tweet.read users.read offline.access',
        'state': 'state',
        'code_challenge': 'challenge',
        'code_challenge_method': 'plain'
    }
    auth_url = f"https://twitter.com/i/oauth2/authorize?{urlencode(params)}"
    return Response({'auth_url': auth_url})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def x_callback(request):
    """Exchanges code for X access token and saves profile"""
    code = request.data.get('code')
    if not code:
        return Response({'error': 'No code provided'}, status=status.HTTP_400_BAD_REQUEST)

    token_url = "https://api.twitter.com/2/oauth2/token"
    data = {
        'code': code,
        'grant_type': 'authorization_code',
        'client_id': settings.X_CLIENT_ID,
        'redirect_uri': settings.X_REDIRECT_URI,
        'code_verifier': 'challenge'
    }
    
    try:
        response = requests.post(token_url, data=data, auth=(settings.X_CLIENT_ID, settings.X_CLIENT_SECRET))
        token_data = response.json()
        
        if 'error' in token_data:
             return Response({'error': token_data.get('error_description', 'Failed')}, status=status.HTTP_400_BAD_REQUEST)
             
        access_token = token_data.get('access_token')
        refresh_token = token_data.get('refresh_token')
        
        me_response = requests.get('https://api.twitter.com/2/users/me', headers={'Authorization': f'Bearer {access_token}'})
        me_data = me_response.json()
        platform_account_id = me_data.get('data', {}).get('id', 'unknown_x_id')
        
        profile, created = SocialProfile.objects.update_or_create(
            user=request.user,
            platform='twitter',
            platform_account_id=platform_account_id,
            defaults={
                'access_token': access_token,
                'refresh_token': refresh_token,
                'token_expires_at': timezone.now() + timedelta(seconds=token_data.get('expires_in', 7200))
            }
        )
        
        return Response({'message': 'X connected successfully', 'profile_id': profile.id})
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
