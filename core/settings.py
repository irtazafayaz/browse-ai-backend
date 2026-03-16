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
    # Django admin + auth
    'django.contrib.admin',
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third-party
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'drf_spectacular',
    # Local
    'accounts',
    'products',
    'blog',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'core.middleware.RequestResponseLogMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'

# ── Database ──────────────────────────────────────────────────────────
# SQLite is used only for Django admin sessions and blog posts (ORM).
# All other app data (users, products, bookmarks) lives in MongoDB via pymongo.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017')
MONGO_DB_NAME = os.environ.get('MONGO_DB_NAME', 'browse_ai')

# ── Authentication ────────────────────────────────────────────────────
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',   # Django admin login
    'accounts.backend.MongoAuthBackend',            # API JWT auth
]

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
_LOG_DIR = BASE_DIR / 'logs'
_LOG_DIR.mkdir(exist_ok=True)

_APP_HANDLERS = ['console', 'file']
_APP_LEVEL    = 'DEBUG' if DEBUG else 'INFO'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'request_id': {'()': 'core.log_filters.RequestIDFilter'},
    },
    'formatters': {
        'console': {'()': 'core.formatters.ConsoleFormatter'},
        'json':    {'()': 'core.formatters.JSONFormatter'},
    },
    'handlers': {
        'console': {
            'class':     'logging.StreamHandler',
            'formatter': 'console',
            'filters':   ['request_id'],
        },
        'file': {
            'class':       'logging.handlers.TimedRotatingFileHandler',
            'filename':    str(_LOG_DIR / 'browse-ai.log'),
            'when':        'midnight',
            'backupCount': 14,
            'encoding':    'utf-8',
            'formatter':   'json',
            'filters':     ['request_id'],
        },
    },
    'root': {
        'handlers': _APP_HANDLERS,
        'level': 'WARNING',
    },
    'loggers': {
        'core':              {'handlers': _APP_HANDLERS, 'level': _APP_LEVEL,  'propagate': False},
        'core.requests':     {'handlers': _APP_HANDLERS, 'level': 'INFO',      'propagate': False},
        'accounts':          {'handlers': _APP_HANDLERS, 'level': _APP_LEVEL,  'propagate': False},
        'products':          {'handlers': _APP_HANDLERS, 'level': _APP_LEVEL,  'propagate': False},
        'products.ai_search':{'handlers': _APP_HANDLERS, 'level': 'INFO',      'propagate': False},
        'blog':              {'handlers': _APP_HANDLERS, 'level': _APP_LEVEL,  'propagate': False},
        'django':            {'handlers': _APP_HANDLERS, 'level': 'WARNING',   'propagate': False},
        'django.server':     {'handlers': _APP_HANDLERS, 'level': 'WARNING',   'propagate': False},
        'django.request':    {'handlers': _APP_HANDLERS, 'level': 'ERROR',     'propagate': False},
        'pymongo':           {'handlers': _APP_HANDLERS, 'level': 'WARNING',   'propagate': False},
    },
}

# ── Misc ──────────────────────────────────────────────────────────────
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True
STATIC_URL = 'static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
