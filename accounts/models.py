import logging
from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId
from django.contrib.auth.hashers import make_password, check_password

from core.db import users_col

logger = logging.getLogger(__name__)


class User:
    """
    MongoDB-backed user. Not a Django ORM model.
    Stores documents in the 'users' collection on Atlas.
    """

    def __init__(self, doc):
        self._id = str(doc['_id'])
        self.id = self._id          # DRF / simplejwt expect .id
        self.pk = self._id          # Django internals expect .pk
        self.email = doc.get('email', '')
        self.first_name = doc.get('first_name', '')
        self.last_name = doc.get('last_name', '')
        self.avatar_url = doc.get('avatar_url', '')
        self.google_id = doc.get('google_id', '')
        self.password = doc.get('password', '')
        self.is_active = doc.get('is_active', True)
        self.is_staff = doc.get('is_staff', False)
        self.is_superuser = doc.get('is_superuser', False)
        self.date_joined = doc.get('date_joined', datetime.now(timezone.utc))
        self.last_login = doc.get('last_login')

    # ── Django auth interface ─────────────────────────────────────────

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def save(self, update_fields=None):
        col = users_col()
        doc = {
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'avatar_url': self.avatar_url,
            'google_id': self.google_id,
            'password': self.password,
            'is_active': self.is_active,
            'is_staff': self.is_staff,
            'is_superuser': self.is_superuser,
            'date_joined': self.date_joined,
            'last_login': self.last_login,
        }
        if update_fields:
            doc = {k: doc[k] for k in update_fields if k in doc}
            col.update_one({'_id': ObjectId(self._id)}, {'$set': doc})
        else:
            col.update_one({'_id': ObjectId(self._id)}, {'$set': doc}, upsert=True)

    def __str__(self):
        return self.email

    # ── Class-level helpers ───────────────────────────────────────────

    @classmethod
    def create(cls, email, password=None, **kwargs):
        logger.info("Creating user: %s", email)
        doc = {
            'email': email.strip().lower(),
            'first_name': kwargs.get('first_name', ''),
            'last_name': kwargs.get('last_name', ''),
            'avatar_url': kwargs.get('avatar_url', ''),
            'google_id': kwargs.get('google_id', ''),
            'password': make_password(password) if password else make_password(None),
            'is_active': kwargs.get('is_active', True),
            'is_staff': kwargs.get('is_staff', False),
            'is_superuser': kwargs.get('is_superuser', False),
            'date_joined': datetime.now(timezone.utc),
            'last_login': None,
        }
        result = users_col().insert_one(doc)
        doc['_id'] = result.inserted_id
        logger.info("User created with id: %s", result.inserted_id)
        return cls(doc)

    @classmethod
    def get_by_email(cls, email):
        logger.debug("Looking up user by email: %s", email)
        doc = users_col().find_one({'email': email.strip().lower()})
        return cls(doc) if doc else None

    @classmethod
    def get_by_id(cls, user_id):
        logger.debug("Looking up user by id: %s", user_id)
        try:
            doc = users_col().find_one({'_id': ObjectId(user_id)})
        except (InvalidId, TypeError):
            logger.warning("Invalid user_id format: %s", user_id)
            return None
        return cls(doc) if doc else None

    @classmethod
    def get_or_create(cls, email, defaults=None):
        existing = cls.get_by_email(email)
        if existing:
            logger.debug("Found existing user: %s", email)
            return existing, False
        kwargs = defaults or {}
        user = cls.create(email=email, **kwargs)
        return user, True
