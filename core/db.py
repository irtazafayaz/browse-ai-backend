"""
Central MongoDB connection and collection accessors.
All apps import from here — no cross-app imports needed.
Indexes are created once at startup via products/apps.py AppConfig.ready().
"""
import os
import logging
import certifi
from pymongo import MongoClient, ASCENDING
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

_client = None


def get_client() -> MongoClient:
    """
    Return a singleton MongoClient.
    Uses certifi's CA bundle so TLS handshakes succeed on Python 3.13+.
    serverSelectionTimeoutMS is kept short so startup failures surface fast.
    """
    global _client
    if _client is None:
        uri = os.environ.get('MONGO_URI', 'mongodb://localhost:27017')
        logger.debug("Creating MongoClient for URI: %s", uri.split('@')[-1])  # mask credentials
        _client = MongoClient(
            uri,
            tlsCAFile=certifi.where(),
            serverSelectionTimeoutMS=5_000,
        )
    return _client


def get_db():
    db_name = os.environ.get('MONGO_DB_NAME', 'browse_ai')
    return get_client()[db_name]


# ── Collection accessors ──────────────────────────────────────────────

def users_col():
    return get_db()['users']


def token_blacklist_col():
    return get_db()['token_blacklist']


def products_col():
    return get_db()['products']


def bookmarks_col():
    return get_db()['bookmarks']


def edits_col():
    return get_db()['edits']


def prompts_col():
    return get_db()['prompts']


# ── Index bootstrap — called once from AppConfig.ready() ─────────────

def ensure_indexes():
    logger.info("Ensuring MongoDB indexes…")
    db = get_db()

    db['users'].create_index([('email', ASCENDING)], unique=True, background=True)

    db['token_blacklist'].create_index([('jti', ASCENDING)], unique=True, background=True)
    db['token_blacklist'].create_index(
        [('expires_at', ASCENDING)], expireAfterSeconds=0, background=True
    )

    db['bookmarks'].create_index(
        [('user_id', ASCENDING), ('product_id', ASCENDING)], unique=True, background=True
    )
    logger.info("MongoDB indexes OK.")
