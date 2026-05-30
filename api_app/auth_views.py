import secrets
from urllib.parse import urlencode

import requests
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import make_password
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .models import CustomUser
from .totp_utils import (
    build_totp_uri,
    generate_totp_secret,
    issue_challenge_token,
    qr_code_data_url,
    read_challenge_token,
    verify_totp_code,
)


def _jwt_response(user):
    refresh = RefreshToken.for_user(user)
    return {
        'status': 'success',
        'access': str(refresh.access_token),
        'refresh': str(refresh),
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'totp_enabled': user.totp_enabled,
        },
    }


def _setup_challenge(user):
    if not user.totp_secret:
        user.totp_secret = generate_totp_secret()
        user.save(update_fields=['totp_secret'])

    uri = build_totp_uri(user, user.totp_secret)
    return Response({
        'status': 'totp_setup_required',
        'challenge_token': issue_challenge_token(user.id, 'setup'),
        'qr_image': qr_code_data_url(uri),
        'manual_key': user.totp_secret,
        'message': 'Scan the QR code with Google Authenticator, then enter the 6-digit code.',
    })


def _verify_challenge(user):
    return Response({
        'status': 'totp_required',
        'challenge_token': issue_challenge_token(user.id, 'verify'),
        'message': 'Enter the 6-digit code from Google Authenticator.',
    })


def _post_auth_response(user):
    if not user.totp_enabled:
        return _setup_challenge(user)
    return _verify_challenge(user)


@api_view(['POST'])
@permission_classes([AllowAny])
def auth_login(request):
    username = (request.data.get('username') or '').strip()
    password = request.data.get('password') or ''

    if not username or not password:
        return Response({'error': 'Username and password are required.'}, status=status.HTTP_400_BAD_REQUEST)

    user = authenticate(username=username, password=password)
    if user is None:
        try:
            user = CustomUser.objects.get(username=username)
            if not user.check_password(password):
                user = None
        except CustomUser.DoesNotExist:
            user = None

    if user is None or not user.is_active:
        return Response({'error': 'Invalid credentials.'}, status=status.HTTP_401_UNAUTHORIZED)

    return _post_auth_response(user)


@api_view(['GET'])
@permission_classes([AllowAny])
def google_auth_url(request):
    client_id = settings.GOOGLE_CLIENT_ID
    redirect_uri = settings.GOOGLE_REDIRECT_URI
    if not client_id or not redirect_uri:
        return Response({'error': 'Google OAuth is not configured.'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    params = {
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'scope': 'openid email profile',
        'access_type': 'online',
        'prompt': 'select_account',
    }
    return Response({'auth_url': f'https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}'})


def _get_or_create_google_user(google_id, email, name):
    user = CustomUser.objects.filter(google_id=google_id).first()
    if user:
        return user

    if email:
        user = CustomUser.objects.filter(email__iexact=email).first()
        if user:
            user.google_id = google_id
            user.save(update_fields=['google_id'])
            return user

    base_username = (email.split('@')[0] if email else f'google_{google_id[:8]}').lower()
    base_username = ''.join(ch for ch in base_username if ch.isalnum() or ch in '._-') or f'user_{google_id[:8]}'
    username = base_username
    suffix = 1
    while CustomUser.objects.filter(username=username).exists():
        username = f'{base_username}{suffix}'
        suffix += 1

    return CustomUser.objects.create(
        username=username,
        email=email or f'{google_id}@google.oauth',
        google_id=google_id,
        company_name=name or username,
        password=make_password(secrets.token_urlsafe(32)),
        is_active=True,
    )


@api_view(['POST'])
@permission_classes([AllowAny])
def google_auth_callback(request):
    code = request.data.get('code')
    if not code:
        return Response({'error': 'Authorization code is required.'}, status=status.HTTP_400_BAD_REQUEST)

    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET or not settings.GOOGLE_REDIRECT_URI:
        return Response({'error': 'Google OAuth is not configured.'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    try:
        token_res = requests.post(
            'https://oauth2.googleapis.com/token',
            data={
                'code': code,
                'client_id': settings.GOOGLE_CLIENT_ID,
                'client_secret': settings.GOOGLE_CLIENT_SECRET,
                'redirect_uri': settings.GOOGLE_REDIRECT_URI,
                'grant_type': 'authorization_code',
            },
            timeout=15,
        )
        token_data = token_res.json()
        if token_res.status_code != 200 or 'access_token' not in token_data:
            err = token_data.get('error_description') or token_data.get('error') or 'Google token exchange failed.'
            return Response({'error': err}, status=status.HTTP_400_BAD_REQUEST)

        profile_res = requests.get(
            'https://www.googleapis.com/oauth2/v3/userinfo',
            headers={'Authorization': f'Bearer {token_data["access_token"]}'},
            timeout=15,
        )
        profile = profile_res.json()
        if profile_res.status_code != 200 or not profile.get('sub'):
            return Response({'error': 'Failed to fetch Google profile.'}, status=status.HTTP_400_BAD_REQUEST)

        user = _get_or_create_google_user(
            google_id=profile['sub'],
            email=profile.get('email'),
            name=profile.get('name'),
        )
        if not user.is_active:
            return Response({'error': 'Account is inactive.'}, status=status.HTTP_403_FORBIDDEN)

        return _post_auth_response(user)
    except requests.RequestException as exc:
        return Response({'error': f'Google OAuth request failed: {exc}'}, status=status.HTTP_502_BAD_GATEWAY)


def _resolve_challenge(request, expected_purpose):
    token = request.data.get('challenge_token') or ''
    code = request.data.get('code') or ''

    user_id, purpose = read_challenge_token(token)
    if user_id is None or purpose != expected_purpose:
        return None, Response({'error': 'Invalid or expired session. Please sign in again.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = CustomUser.objects.get(pk=user_id, is_active=True)
    except CustomUser.DoesNotExist:
        return None, Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

    if not verify_totp_code(user.totp_secret, code):
        return None, Response({'error': 'Invalid verification code.'}, status=status.HTTP_400_BAD_REQUEST)

    return user, None


@api_view(['POST'])
@permission_classes([AllowAny])
def totp_confirm_setup(request):
    user, error = _resolve_challenge(request, 'setup')
    if error:
        return error

    user.totp_enabled = True
    user.save(update_fields=['totp_enabled'])
    return Response(_jwt_response(user))


@api_view(['POST'])
@permission_classes([AllowAny])
def totp_verify(request):
    user, error = _resolve_challenge(request, 'verify')
    if error:
        return error

    return Response(_jwt_response(user))
