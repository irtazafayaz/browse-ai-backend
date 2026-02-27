from django.conf import settings
from django.contrib.auth import get_user_model, authenticate
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests as google_requests

from .serializers import (
    RegisterSerializer, UserSerializer,
    TokenPairSerializer, GoogleAuthSerializer,
)

User = get_user_model()


# ── Register ──────────────────────────────────────────────────────────
@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """
    POST /api/auth/register/
    Body: { email, first_name, last_name, password, password2 }
    Returns: { access, refresh, user }
    """
    serializer = RegisterSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    user = serializer.save()
    return Response(TokenPairSerializer.for_user(user), status=status.HTTP_201_CREATED)


# ── Login ─────────────────────────────────────────────────────────────
@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """
    POST /api/auth/login/
    Body: { email, password }
    Returns: { access, refresh, user }
    """
    email = request.data.get('email', '').strip().lower()
    password = request.data.get('password', '')

    if not email or not password:
        return Response(
            {'detail': 'Email and password are required.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user = authenticate(request, email=email, password=password)
    if user is None:
        return Response(
            {'detail': 'Invalid credentials.'},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    return Response(TokenPairSerializer.for_user(user))


# ── Logout (blacklist refresh token) ──────────────────────────────────
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """
    POST /api/auth/logout/
    Body: { refresh }
    Blacklists the refresh token so it can't be reused.
    """
    refresh_token = request.data.get('refresh')
    if not refresh_token:
        return Response({'detail': 'Refresh token required.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        token = RefreshToken(refresh_token)
        token.blacklist()
    except TokenError as e:
        return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    return Response({'detail': 'Logged out successfully.'})


# ── Me (current user profile) ─────────────────────────────────────────
@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def me(request):
    """
    GET  /api/auth/me/ — return current user
    PATCH /api/auth/me/ — update first_name / last_name
    """
    if request.method == 'GET':
        return Response(UserSerializer(request.user).data)

    serializer = UserSerializer(request.user, data=request.data, partial=True)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    serializer.save()
    return Response(serializer.data)


# ── Google OAuth ──────────────────────────────────────────────────────
@api_view(['POST'])
@permission_classes([AllowAny])
def google_auth(request):
    """
    POST /api/auth/google/
    Body: { id_token: "<Google id_token from frontend>" }

    Verifies the Google id_token, then:
    - If user exists → login
    - If user doesn't exist → create account + login
    Returns: { access, refresh, user }

    Frontend flow (Next.js + @react-oauth/google):
    1. User clicks "Sign in with Google" → Google returns id_token
    2. Frontend sends id_token to this endpoint
    3. Backend verifies + returns JWT pair
    """
    serializer = GoogleAuthSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    raw_token = serializer.validated_data['id_token']
    client_id = settings.GOOGLE_CLIENT_ID

    if not client_id:
        return Response(
            {'detail': 'Google OAuth is not configured on this server.'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    # Verify token with Google
    try:
        idinfo = google_id_token.verify_oauth2_token(
            raw_token,
            google_requests.Request(),
            client_id,
        )
    except ValueError as e:
        return Response({'detail': f'Invalid Google token: {e}'}, status=status.HTTP_400_BAD_REQUEST)

    google_id = idinfo['sub']
    email = idinfo.get('email', '')
    first_name = idinfo.get('given_name', '')
    last_name = idinfo.get('family_name', '')
    avatar_url = idinfo.get('picture', '')

    if not email:
        return Response({'detail': 'Google account has no email.'}, status=status.HTTP_400_BAD_REQUEST)

    # Get or create user
    user, created = User.objects.get_or_create(
        email=email,
        defaults={
            'first_name': first_name,
            'last_name': last_name,
            'avatar_url': avatar_url,
            'google_id': google_id,
            'is_active': True,
        },
    )

    # Update google_id / avatar if this is an existing user logging in via Google
    if not created:
        updated = False
        if not user.google_id:
            user.google_id = google_id
            updated = True
        if avatar_url and user.avatar_url != avatar_url:
            user.avatar_url = avatar_url
            updated = True
        if updated:
            user.save(update_fields=['google_id', 'avatar_url'])

    return Response(
        TokenPairSerializer.for_user(user),
        status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
    )
