"""odyssey URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path("odyssey/admin/", admin.site.urls),
    # API
    path("odcwebapi/accounts/", include("accounts.urls"), name="accounts"),
    path("odcwebapi/core/", include("core.urls"), name="core"),
    path("odcwebapi/users/", include("users.urls"), name="users"),
    path("odcwebapi/vanguard/", include("vanguard.urls"), name="vanguard"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


admin.site.site_header = "Top Choice International Admin"
admin.site.site_title = "Top Choice International"
admin.site.index_title = "Welcome to Top Choice International Admin"
admin.autodiscover()
