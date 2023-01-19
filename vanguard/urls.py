from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainSlidingView,
)

from vanguard.api import (
    WhoAmIView,
    AuthAdminLoginView,
    AuthLoginView,
    LogoutView,
    AuthRefreshView,
    RequestResetPasswordView,
)

urlpatterns = [
    path("odclogin/", AuthAdminLoginView.as_view()),
    path("login/", AuthLoginView.as_view()),
    path("whoami/", WhoAmIView.as_view()),
    path("logout/", LogoutView.as_view()),
    path("refresh/", AuthRefreshView.as_view()),
    path("slide/", TokenObtainSlidingView.as_view()),
    path("requestresetpassword/", RequestResetPasswordView.as_view()),
]
