import os
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get(
    'SECRET_KEY', 'dev-insecure-key-change-in-production')
DEBUG = os.environ.get('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = ['*']

# ── Apps ──────────────────────────────────────────────────────────────
INSTALLED_APPS = [
    # Required by simplejwt — auth + contenttypes must both be present.
    # AUTH_USER_MODEL is intentionally NOT set; Django uses its default
    # auth.User ORM model only to satisfy internal checks.
    # Our actual User class in accounts/models.py is a plain Python class
    # backed by MongoDB — it is NOT registered as a Django ORM model.
    'django.contrib.contenttypes',
    'django.contrib.auth',
    # Third-party
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'drf_spectacular',
    # Local
    'accounts',
    'products',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'core.middleware.RequestResponseLogMiddleware',
    'django.middleware.common.CommonMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {'context_processors': []},
    },
]

WSGI_APPLICATION = 'core.wsgi.application'

# ── Database — MongoDB only, no SQLite ───────────────────────────────
# Django ORM is not used. All data lives in MongoDB Atlas via pymongo.
DATABASES = {}

MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017')
MONGO_DB_NAME = os.environ.get('MONGO_DB_NAME', 'browse_ai')

# ── Authentication ────────────────────────────────────────────────────
AUTHENTICATION_BACKENDS = ['accounts.backend.MongoAuthBackend']

# ── Password validation ────────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ── DRF ───────────────────────────────────────────────────────────────
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'accounts.jwt_auth.MongoJWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/day',
        'user': '1000/day',
        'auth': '10/min',
    },
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# ── OpenAPI / Swagger ─────────────────────────────────────────────────
SPECTACULAR_SETTINGS = {
    'TITLE': 'Browse AI API',
    'DESCRIPTION': (
        'REST API for Browse AI — an AI-powered product discovery platform.\n\n'
        '## Authentication\n'
        'Most endpoints are public. Endpoints marked **🔒 Requires Auth** need a Bearer JWT.\n\n'
        '1. Call `POST /api/auth/register/` or `POST /api/auth/login/` to obtain tokens.\n'
        '2. Click **Authorize** (top right) and enter: `Bearer <access_token>`\n'
        '3. Access tokens expire in **15 minutes**. Use `POST /api/auth/token/refresh/` to rotate.\n\n'
        '## Rate Limits\n'
        '- Anonymous: 100 req/day\n'
        '- Authenticated: 1000 req/day\n'
        '- Auth endpoints (register/login): 10 req/min'
    ),
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'SECURITY': [{'BearerAuth': []}],
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        'persistAuthorization': True,
        'displayRequestDuration': True,
        'defaultModelsExpandDepth': 2,
        'defaultModelExpandDepth': 2,
    },
    'TAGS': [
        {'name': 'Auth', 'description': 'Registration, login, logout, and token management'},
        {'name': 'Products', 'description': 'Browse, search, and manage products'},
        {'name': 'Bookmarks', 'description': 'Save and retrieve bookmarked products'},
        {'name': 'Collections',
            'description': 'Curated editorial collections and search prompts'},
    ],
    'SERVERS': [
        {'url': 'http://localhost:8000', 'description': 'Local development'},
    ],
    'SECURITY_DEFINITIONS': {
        'BearerAuth': {
            'type': 'http',
            'scheme': 'bearer',
            'bearerFormat': 'JWT',
            'description': (
                'Enter your access token in the format: `Bearer <token>`\n\n'
                'Obtain a token from `POST /api/auth/login/` or `POST /api/auth/register/`.'
            ),
        }
    },
}

# ── JWT ───────────────────────────────────────────────────────────────
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
    # Blacklisting is handled manually via MongoDB — not via ORM
    'BLACKLIST_AFTER_ROTATION': False,
}

# ── CORS ──────────────────────────────────────────────────────────────
CORS_ALLOWED_ORIGINS = [
    o.strip()
    for o in os.environ.get('CORS_ALLOWED_ORIGINS', 'http://localhost:3000').split(',')
]
CORS_ALLOW_CREDENTIALS = True

# ── Google OAuth ──────────────────────────────────────────────────────
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')

# ── BrowseBy AI ───────────────────────────────────────────────────────
BROWSEBY_API_KEY = os.environ.get('BROWSEBY_API_KEY', '')

# ── Logging ───────────────────────────────────────────────────────────
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} {name}: {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
    'loggers': {
        # ── Our app modules ─────────────────────────────────────────────
        'core': {
            'handlers': ['console'],
            'level': 'DEBUG' if DEBUG else 'WARNING',
            'propagate': False,
        },
        # Incoming request / response interceptor (core/middleware.py)
        'core.requests': {
            'handlers': ['console'],
            'level': 'INFO',   # always log in both dev and prod
            'propagate': False,
        },
        'accounts': {
            'handlers': ['console'],
            'level': 'DEBUG' if DEBUG else 'WARNING',
            'propagate': False,
        },
        'products': {
            'handlers': ['console'],
            'level': 'DEBUG' if DEBUG else 'WARNING',
            'propagate': False,
        },
        # Outgoing BrowseBy AI API interceptor (products/ai_search.py)
        'products.ai_search': {
            'handlers': ['console'],
            'level': 'INFO',   # always log in both dev and prod
            'propagate': False,
        },
        # ── Silence noisy Django internals ──────────────────────────────
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'pymongo': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}

# ── Misc ──────────────────────────────────────────────────────────────
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True
STATIC_URL = 'static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
