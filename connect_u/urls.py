from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('connect_u_app.urls')),
    path('oauth/', include('social_django.urls', namespace='social')),
    # path('', include('django.contrib.auth.urls')),
    path('api/v1/auth/', include('rest_framework_simplejwt.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)