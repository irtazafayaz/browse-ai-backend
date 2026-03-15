from django.urls import path
from . import views

urlpatterns = [
    path('', views.post_list, name='blog-list'),
    path('<slug:slug>/', views.post_detail, name='blog-detail'),
]
