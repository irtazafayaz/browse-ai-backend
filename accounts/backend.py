from .models import User


class MongoAuthBackend:
    """
    Custom Django authentication backend.
    Authenticates against the MongoDB 'users' collection.
    """

    def authenticate(self, request, email=None, password=None, **kwargs):
        if not email or not password:
            return None
        user = User.get_by_email(email)
        if user and user.is_active and user.check_password(password):
            return user
        return None

    def get_user(self, user_id):
        return User.get_by_id(user_id)
