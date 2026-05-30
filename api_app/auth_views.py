from django.contrib.auth import authenticate
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
        'message': 'Scan the QR code with your authenticator app, then enter the 6-digit code.',
    })


def _verify_challenge(user):
    return Response({
        'status': 'totp_required',
        'challenge_token': issue_challenge_token(user.id, 'verify'),
        'message': 'Enter the 6-digit code from your authenticator app.',
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
