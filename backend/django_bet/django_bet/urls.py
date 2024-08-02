from django.contrib import admin
from django.urls import path, include

from drf_yasg import openapi
from drf_yasg.views import get_schema_view as swagger_get_schema_view

schema_view = swagger_get_schema_view(
    openapi.Info(
        title="BetAPP API",
        default_version="v1",
        description="API documentation of Bet App"
    ),
    public=True,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('api.urls')),
    path('api/v1/swagger/schema/', schema_view.with_ui('swagger', cache_timeout=0), name='swagger-schema'),
    path('', schema_view.with_ui('swagger', cache_timeout=0), name='swagger-schema'),
]