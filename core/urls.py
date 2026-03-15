from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns = [
    path('api/auth/', include('accounts.urls')),
    path('api/products/', include('products.urls')),
    path('api/blog/', include('blog.urls')),

    # OpenAPI schema (JSON)
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    # Swagger UI
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'),
         name='swagger-ui'),
    # ReDoc (alternative)
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
