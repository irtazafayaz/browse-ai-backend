from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='auth-register'),
    path('login/', views.login, name='auth-login'),
    path('logout/', views.logout, name='auth-logout'),
    path('token/refresh/', views.token_refresh, name='token-refresh'),
    path('google/', views.google_auth, name='auth-google'),
    path('me/', views.me, name='auth-me'),
]
