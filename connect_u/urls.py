from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('connect_u_app.urls')),
    path('oauth/', include('social_django.urls', namespace='social')),
    path('api/v1/', include('connect_u_app.api_urls')),
    # path('', include('django.contrib.auth.urls')),

    path('api/v1/schema/', SpectacularAPIView.as_view(), name='schema'),
    # Swagger UI:
    path('api/v1/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    # ReDoc UI:
    path('api/v1/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)