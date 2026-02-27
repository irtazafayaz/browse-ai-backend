from django.urls import path
from . import views

urlpatterns = [
    path('', views.product_list, name='product-list'),
    path('search/', views.product_search, name='product-search'),
    path('bookmarks/', views.user_bookmarks, name='user-bookmarks'),
    path('<str:product_id>/', views.product_detail, name='product-detail'),
    path('<str:product_id>/bookmark/', views.toggle_bookmark, name='toggle-bookmark'),
]
