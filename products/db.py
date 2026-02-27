"""
Lightweight MongoDB connection helper.
Returns the browse_ai database client.
All product/bookmark data lives in MongoDB collections.
Django's ORM (SQLite) is only used for auth/admin/sessions.
"""
from django.conf import settings
from pymongo import MongoClient

_client = None


def get_db():
    global _client
    if _client is None:
        _client = MongoClient(settings.MONGO_URI)
    return _client[settings.MONGO_DB_NAME]


def products_col():
    return get_db()['products']


def bookmarks_col():
    return get_db()['bookmarks']
