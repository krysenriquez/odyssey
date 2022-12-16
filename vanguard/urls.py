from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from vanguard.api import WhoAmIView, AuthLoginView, LogoutView

urlpatterns = [
    path("login/", AuthLoginView.as_view()),
    path("whoami/", WhoAmIView.as_view()),
    path("logout/", LogoutView.as_view()),
    path("refresh/", TokenRefreshView.as_view()),
]
