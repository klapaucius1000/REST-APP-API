from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
	path('admin/', admin.site.urls),
	path('api/schema/', SpectacularAPIView.as_view(), name='api_schema'),
	path('api/docs/', SpectacularSwaggerView.as_view(url_name='api_schema'), name='api_docs', ),
	path('api/user/', include('user.urls')),
	path('api/book/', include('book.urls')),
]


if settings.DEBUG:
	urlpatterns += static(
		settings.MEDIA_URL,
		document_root=settings.MEDIA_ROOT,
	)