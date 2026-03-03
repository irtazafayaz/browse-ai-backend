from .serializers import (
    RegisterSerializer, UserSerializer,
    TokenPairSerializer, GoogleAuthSerializer,
)
from .jwt_auth import RefreshToken
from .models import User
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
import logging

from django.conf import settings
from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse, inline_serializer
from rest_framework import serializers as drf_serializers

logger = logging.getLogger(__name__)


@extend_schema(
    tags=['Auth'],
    summary='Register a new user',
    description='Creates a new user account and returns a JWT token pair.',
    request=RegisterSerializer,
    responses={
        201: OpenApiResponse(
            response=TokenPairSerializer,
            description='Account created. Returns access/refresh tokens and user profile.',
            examples=[
                OpenApiExample(
                    'Success',
                    value={
                        'access': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...',
                        'refresh': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...',
                        'user': {
                            'id': '64f1a2b3c4d5e6f7a8b9c0d1',
                            'email': 'jane@example.com',
                            'first_name': 'Jane',
                            'last_name': 'Doe',
                            'avatar_url': '',
                        },
                    },
                )
            ],
        ),
        400: OpenApiResponse(description='Validation error (e.g. email taken, passwords mismatch)'),
    },
    examples=[
        OpenApiExample(
            'Register request',
            value={
                'email': 'jane@example.com',
                'first_name': 'Jane',
                'last_name': 'Doe',
                'password': 'StrongPass123!',
                'password2': 'StrongPass123!',
            },
            request_only=True,
        )
    ],
)
@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([ScopedRateThrottle])
def register(request):
    request.throttle_scope = 'auth'
    serializer = RegisterSerializer(data=request.data)
    if not serializer.is_valid():
        logger.debug("Register validation failed: %s", serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data
    if User.get_by_email(data['email']):
        logger.info("Register rejected — email already exists: %s",
                    data['email'])
        return Response({'email': 'A user with this email already exists.'}, status=status.HTTP_400_BAD_REQUEST)

    user = User.create(
        email=data['email'],
        password=data['password'],
        first_name=data.get('first_name', ''),
        last_name=data.get('last_name', ''),
    )
    logger.info("New user registered: %s (id=%s)", user.email, user.id)
    return Response(TokenPairSerializer.for_user(user), status=status.HTTP_201_CREATED)


@extend_schema(
    tags=['Auth'],
    summary='Login',
    description='Authenticate with email and password. Returns a JWT token pair.',
    request=inline_serializer(
        name='LoginRequest',
        fields={
            'email': drf_serializers.EmailField(),
            'password': drf_serializers.CharField(),
        },
    ),
    responses={
        200: OpenApiResponse(
            response=TokenPairSerializer,
            description='Login successful.',
            examples=[
                OpenApiExample(
                    'Success',
                    value={
                        'access': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...',
                        'refresh': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...',
                        'user': {
                            'id': '64f1a2b3c4d5e6f7a8b9c0d1',
                            'email': 'jane@example.com',
                            'first_name': 'Jane',
                            'last_name': 'Doe',
                            'avatar_url': '',
                        },
                    },
                )
            ],
        ),
        400: OpenApiResponse(description='Missing email or password.'),
        401: OpenApiResponse(description='Invalid credentials.'),
    },
    examples=[
        OpenApiExample(
            'Login request',
            value={'email': 'jane@example.com', 'password': 'StrongPass123!'},
            request_only=True,
        )
    ],
)
@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([ScopedRateThrottle])
def login(request):
    request.throttle_scope = 'auth'
    email = request.data.get('email', '').strip().lower()
    password = request.data.get('password', '')

    if not email or not password:
        return Response(
            {'detail': 'Email and password are required.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user = authenticate(request, email=email, password=password)
    if user is None:
        logger.info("Failed login attempt for email: %s", email)
        return Response(
            {'detail': 'Invalid credentials.'},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    logger.info("User logged in: %s (id=%s)", user.email, user.id)
    return Response(TokenPairSerializer.for_user(user))


@extend_schema(
    tags=['Auth'],
    summary='Logout',
    description='Blacklists the provided refresh token so it can no longer be used.',
    request=inline_serializer(
        name='LogoutRequest',
        fields={'refresh': drf_serializers.CharField()},
    ),
    responses={
        200: OpenApiResponse(
            description='Logged out successfully.',
            examples=[OpenApiExample(
                'Success', value={'detail': 'Logged out successfully.'})],
        ),
        400: OpenApiResponse(description='Missing or invalid refresh token.'),
    },
    examples=[
        OpenApiExample(
            'Logout request',
            value={'refresh': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'},
            request_only=True,
        )
    ],
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    refresh_token = request.data.get('refresh')
    if not refresh_token:
        return Response({'detail': 'Refresh token required.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        token = RefreshToken(refresh_token)
        token.blacklist()
    except TokenError as e:
        logger.warning("Logout failed — invalid token: %s", e)
        return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    logger.info("User logged out (token blacklisted)")
    return Response({'detail': 'Logged out successfully.'})


@extend_schema(
    tags=['Auth'],
    summary='Get or update current user',
    description=(
        '**GET** — Returns the authenticated user\'s profile.\n\n'
        '**PATCH** — Updates `first_name` and/or `last_name`. All fields are optional.'
    ),
    request=UserSerializer,
    responses={
        200: OpenApiResponse(
            response=UserSerializer,
            description='User profile.',
            examples=[
                OpenApiExample(
                    'User profile',
                    value={
                        'id': '64f1a2b3c4d5e6f7a8b9c0d1',
                        'email': 'jane@example.com',
                        'first_name': 'Jane',
                        'last_name': 'Doe',
                        'avatar_url': 'https://lh3.googleusercontent.com/a/...',
                    },
                )
            ],
        ),
        400: OpenApiResponse(description='Validation error.'),
        401: OpenApiResponse(description='Authentication required.'),
    },
    examples=[
        OpenApiExample(
            'Update name',
            value={'first_name': 'Janet', 'last_name': 'Smith'},
            request_only=True,
        )
    ],
)
@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def me(request):
    if request.method == 'GET':
        return Response(UserSerializer(request.user).data)

    serializer = UserSerializer(request.user, data=request.data, partial=True)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    serializer.update(request.user, serializer.validated_data)
    return Response(UserSerializer(request.user).data)


@extend_schema(
    tags=['Auth'],
    summary='Google OAuth sign-in',
    description=(
        'Authenticate using a Google `id_token` obtained from the Google Sign-In SDK.\n\n'
        'If the email does not exist, a new account is created (HTTP 201).\n'
        'If the email already exists, the existing account is returned (HTTP 200).'
    ),
    request=GoogleAuthSerializer,
    responses={
        200: OpenApiResponse(response=TokenPairSerializer, description='Existing user authenticated.'),
        201: OpenApiResponse(response=TokenPairSerializer, description='New user created via Google.'),
        400: OpenApiResponse(description='Invalid or missing Google id_token.'),
        503: OpenApiResponse(description='Google OAuth not configured on this server.'),
    },
    examples=[
        OpenApiExample(
            'Google auth request',
            value={'id_token': 'eyJhbGciOiJSUzI1NiIsImtpZCI6Ii4uLiJ9...'},
            request_only=True,
        )
    ],
)
@api_view(['POST'])
@permission_classes([AllowAny])
def google_auth(request):
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

    user, created = User.get_or_create(
        email=email,
        defaults={
            'first_name': first_name,
            'last_name': last_name,
            'avatar_url': avatar_url,
            'google_id': google_id,
            'is_active': True,
        },
    )

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


@extend_schema(
    tags=['Auth'],
    summary='Refresh access token',
    description=(
        'Exchange a valid refresh token for a new access + refresh token pair.\n\n'
        'The old refresh token is **blacklisted** immediately (token rotation).'
    ),
    request=inline_serializer(
        name='TokenRefreshRequest',
        fields={'refresh': drf_serializers.CharField()},
    ),
    responses={
        200: OpenApiResponse(
            response=inline_serializer(
                name='TokenRefreshResponse',
                fields={
                    'access': drf_serializers.CharField(),
                    'refresh': drf_serializers.CharField(),
                },
            ),
            description='New token pair.',
            examples=[
                OpenApiExample(
                    'Success',
                    value={
                        'access': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...',
                        'refresh': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...',
                    },
                )
            ],
        ),
        400: OpenApiResponse(description='Refresh token missing.'),
        401: OpenApiResponse(description='Token is invalid or expired.'),
    },
    examples=[
        OpenApiExample(
            'Refresh request',
            value={'refresh': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'},
            request_only=True,
        )
    ],
)
@api_view(['POST'])
@permission_classes([AllowAny])
def token_refresh(request):
    raw = request.data.get('refresh')
    if not raw:
        return Response({'detail': 'Refresh token required.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        token = RefreshToken(raw)
        access = str(token.access_token)
        token.blacklist()
        new_refresh = RefreshToken.for_user_id(str(token['user_id']))
        logger.debug("Token refreshed for user_id: %s", token['user_id'])
        return Response({'access': access, 'refresh': str(new_refresh)})
    except (TokenError, InvalidToken) as e:
        logger.warning("Token refresh failed: %s", e)
        return Response({'detail': str(e)}, status=status.HTTP_401_UNAUTHORIZED)
