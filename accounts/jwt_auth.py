"""
Custom JWT authentication + token blacklist backed by MongoDB.
Replaces rest_framework_simplejwt.token_blacklist (which needs Django ORM).
"""
import logging
from datetime import datetime, timezone

from drf_spectacular.extensions import OpenApiAuthenticationExtension

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import RefreshToken as _RefreshToken

from core.db import token_blacklist_col
from .models import User

logger = logging.getLogger(__name__)


class MongoJWTAuthentication(JWTAuthentication):
    """
    Extends simplejwt's JWTAuthentication to:
    - Load the user from MongoDB instead of Django ORM
    - Check the token against our MongoDB blacklist
    """

    def get_user(self, validated_token):
        user_id = validated_token.get('user_id')
        if not user_id:
            logger.warning("JWT has no user_id claim")
            raise InvalidToken(
                'Token contained no recognisable user identification')

        jti = validated_token.get('jti')
        if jti and token_blacklist_col().find_one({'jti': jti}):
            logger.warning("Blacklisted token used (jti=%s)", jti)
            raise InvalidToken('Token has been blacklisted')

        user = User.get_by_id(str(user_id))
        if user is None:
            logger.warning("JWT references unknown user_id: %s", user_id)
            raise InvalidToken('User not found')
        if not user.is_active:
            logger.warning("JWT used by inactive user: %s", user_id)
            raise InvalidToken('User is inactive')
        return user


class RefreshToken(_RefreshToken):
    """
    Wraps simplejwt RefreshToken to blacklist via MongoDB instead of ORM.
    """

    def blacklist(self):
        jti = self.payload.get('jti')
        exp = self.payload.get('exp')
        if not jti:
            raise TokenError('Token has no jti claim')

        expires_at = datetime.fromtimestamp(
            exp, tz=timezone.utc) if exp else None
        try:
            result = token_blacklist_col().update_one(
                {'jti': jti},
                {'$set': {'jti': jti, 'expires_at': expires_at,
                          'blacklisted_at': datetime.now(timezone.utc)}},
                upsert=True,
            )
            if result.matched_count == 0 and result.upserted_id is None:
                logger.error("Blacklist write produced no effect for jti=%s", jti)
                raise TokenError('Failed to blacklist token')
        except TokenError:
            raise
        except Exception as e:
            logger.error("Blacklist write failed for jti=%s: %s", jti, e)
            raise TokenError('Failed to blacklist token due to storage error')

    @classmethod
    def for_user(cls, user):
        token = super().for_user(user)
        # simplejwt uses token['user_id'] — set it to the string _id
        token['user_id'] = str(user.id)
        return token

    @classmethod
    def for_user_id(cls, user_id: str):
        """Create a refresh token for a user_id string (used during rotation).
        Validates the user still exists before issuing the token."""
        if not user_id:
            raise TokenError('user_id is required')
        # Verify user still exists — prevents issuing tokens for deleted accounts
        user = User.get_by_id(user_id)
        if user is None:
            raise TokenError('User no longer exists')
        if not user.is_active:
            raise TokenError('User account is inactive')
        token = cls()
        token['user_id'] = user_id
        return token


class MongoJWTAuthenticationScheme(OpenApiAuthenticationExtension):
    """Teach drf-spectacular how to document MongoJWTAuthentication."""
    target_class = 'accounts.jwt_auth.MongoJWTAuthentication'
    name = 'BearerAuth'

    def get_security_definition(self, auto_schema):
        return {
            'type': 'http',
            'scheme': 'bearer',
            'bearerFormat': 'JWT',
            'description': (
                'JWT Bearer token. Obtain one from `POST /api/auth/login/` '
                'or `POST /api/auth/register/`, then enter it as: `Bearer <token>`'
            ),
        }
