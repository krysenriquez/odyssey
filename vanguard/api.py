import jwt
import os
from django.conf import settings
from django.template.loader import render_to_string
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from rest_framework import status, views
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenObtainSlidingView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from core.services import send_email
from vanguard.serializers import (
    AuthAdminLoginSerializer,
    AuthLoginSerializer,
    AuthRefreshSerializer,
)
from vanguard.permissions import *
from accounts.models import Account
from users.models import User
from vanguard.services import create_reset_password_link, verify_reset_password_link


class AuthAdminLoginView(TokenObtainPairView):
    serializer_class = AuthAdminLoginSerializer


class AuthLoginView(TokenObtainPairView):
    serializer_class = AuthLoginSerializer


class AuthRefreshView(TokenRefreshView):
    serializer_class = AuthRefreshSerializer


class WhoAmIView(views.APIView):
    def post(self, request, *args, **kwargs):
        data = {
            "user_id": request.user.user_id,
            "email_address": request.user.email_address,
            "username": request.user.username,
            "user_type": request.user.user_type,
            "ccu": request.user.can_change_username,
            "cce": request.user.can_change_email_address,
            "ccp": request.user.can_change_password,
        }

        if request.user.user_type == UserType.MEMBER:
            account = Account.objects.get(user=request.user)
            data["user_avatar"] = request.build_absolute_uri("/") + account.avatar_info.file_attachment.url

        return Response(
            data=data,
            status=status.HTTP_200_OK,
        )


class LogoutView(views.APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        if self.request.data.get("all"):
            token: OutstandingToken
            for token in OutstandingToken.objects.filter(user=request.user):
                _, _ = BlacklistedToken.objects.get_or_create(token=token)
            return Response({"status": "OK, goodbye, all refresh tokens blacklisted"})
        refresh_token = self.request.data.get("refresh_token")
        token = RefreshToken(token=refresh_token)
        token.blacklist()
        return Response({"status": "OK, goodbye"})


class RequestResetPasswordView(views.APIView):
    permission_classes = []

    def get(self, request, *args, **kwargs):
        data = self.request.query_params.get("data", None)
        is_verified, unsigned_obj = verify_reset_password_link(data)
        if is_verified:
            user = User.objects.get(id=unsigned_obj["user"])
            refresh = RefreshToken.for_user(user)
            return Response(
                {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                },
                status=status.HTTP_200_OK,
            )
        return Response(
            data={"message": unsigned_obj},
            status=status.HTTP_400_BAD_REQUEST,
        )

    def post(self, request, *args, **kwargs):
        email_address = request.data.get("recovery_email")
        try:
            validate_email(email_address)
            try:
                user = User.objects.exclude(user_type=UserType.MEMBER).get(email_address=email_address)
            except User.DoesNotExist:
                return Response(
                    data={"message": "Invalid Recovery Email Address"},
                    status=status.HTTP_404_NOT_FOUND,
                )
            else:
                reset_password_link = create_reset_password_link(request, user)
                msg_html = render_to_string(
                    "forgot-password.html", {"username": user.username, "reset_password_link": reset_password_link}
                )
                message = send_email("Reset Password", msg_html, user.email_address)
                return Response(
                    data={"message": message},
                    status=status.HTTP_200_OK,
                )
        except ValidationError:
            return Response(
                data={"message": "Please enter a valid Email Address format."},
                status=status.HTTP_400_BAD_REQUEST,
            )
