from django.contrib import admin
from django.urls import include, path
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/refresh/", TokenRefreshView.as_view()),
    path("api/", include("crm.urls")),
]
