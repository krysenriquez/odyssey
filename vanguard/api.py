from rest_framework import status, views
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from users.enums import *
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from vanguard.serializers import AuthLoginSerializer
from vanguard.permissions import *


class AuthLoginView(TokenObtainPairView):
    serializer_class = AuthLoginSerializer


class WhoAmIView(views.APIView):
    def post(self, request, *args, **kwargs):
        return Response(
            data={
                "userId": request.user.user_id,
                "username": request.user.username,
                "userType": request.user.user_type,
            },
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
