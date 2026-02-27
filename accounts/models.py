from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom user model.
    - Uses email as the login identifier instead of username.
    - avatar_url stores a Google profile picture URL for OAuth users.
    - google_id links the account to a Google OAuth identity.
    """
    username = None  # remove username field
    email = models.EmailField(unique=True)
    avatar_url = models.URLField(blank=True, default='')
    google_id = models.CharField(max_length=128, blank=True, default='')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []  # email is already required via USERNAME_FIELD

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.email
