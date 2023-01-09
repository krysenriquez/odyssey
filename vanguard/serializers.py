from django.db.models import Q
from django.contrib.auth import get_user_model, authenticate
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework_simplejwt.state import token_backend
from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer,
    TokenObtainSerializer,
    TokenRefreshSerializer,
    TokenObtainSlidingSerializer
)
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status, exceptions
from users.enums import UserType
from users.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ("id", "username", "email_address")

class AuthAdminLoginSerializer(TokenObtainPairSerializer, TokenObtainSerializer):
    def get_token(cls, user):
        token = super().get_token(user)
        token["name"] = user.username
        token["email_address"] = user.email_address
        token["user_type"] = user.user_type

        return token

    def validate(self, attrs):
        authenticate_kwargs = {
            self.username_field: attrs[self.username_field],
            "password": attrs["password"],
        }
        try:
            authenticate_kwargs["request"] = self.context["request"]
        except KeyError:
            pass

        """
        Checking if the user exists by getting the email(username field) from authentication_kwargs.
        If the user exists we check if the user account is active.
        If the user account is not active we raise the exception and pass the message. 
        Thus stopping the user from getting authenticated altogether. 
        
        And if the user does not exist at all we raise an exception with a different error message.
        Thus stopping the execution righ there.  
        """
        try:
            user = User.objects.get(~Q(user_type=UserType.MEMBER), username=authenticate_kwargs["username"])
            if not user.is_active:
                self.error_messages["no_active_account"] = _("Account has been deactivated")
                raise exceptions.AuthenticationFailed(
                    self.error_messages["no_active_account"],
                    "no_active_account",
                )
        except User.DoesNotExist:
            self.error_messages["no_active_account"] = _("Account does not exist")
            raise exceptions.AuthenticationFailed(
                self.error_messages["no_active_account"],
                "no_active_account",
            )

        """
        We come here if everything above goes well.
        Here we authenticate the user.
        The authenticate function return None if the credentials do not match 
        or the user account is inactive. However here we can safely raise the exception
        that the credentials did not match as we do all the checks above this point.
        """
        self.user = authenticate(**authenticate_kwargs)
        if self.user is None:
            self.error_messages["no_active_account"] = _("Credentials did not match")
            raise exceptions.AuthenticationFailed(
                self.error_messages["no_active_account"],
                "no_active_account",
            )
        return super().validate(attrs)


class AuthLoginSerializer(TokenObtainPairSerializer, TokenObtainSerializer):
    def get_token(cls, user):
        token = super().get_token(user)
        token["name"] = user.username
        token["email_address"] = user.email_address
        token["user_type"] = user.user_type

        return token

    def validate(self, attrs):
        authenticate_kwargs = {
            self.username_field: attrs[self.username_field],
            "password": attrs["password"],
        }
        try:
            authenticate_kwargs["request"] = self.context["request"]
        except KeyError:
            pass

        """
        Checking if the user exists by getting the email(username field) from authentication_kwargs.
        If the user exists we check if the user account is active.
        If the user account is not active we raise the exception and pass the message. 
        Thus stopping the user from getting authenticated altogether. 
        
        And if the user does not exist at all we raise an exception with a different error message.
        Thus stopping the execution righ there.  
        """
        try:
            user = User.objects.get(username=authenticate_kwargs["username"])
            if not user.is_active:
                self.error_messages["no_active_account"] = _("Account has been deactivated")
                raise exceptions.AuthenticationFailed(
                    self.error_messages["no_active_account"],
                    "no_active_account",
                )
        except User.DoesNotExist:
            self.error_messages["no_active_account"] = _("Account does not exist")
            raise exceptions.AuthenticationFailed(
                self.error_messages["no_active_account"],
                "no_active_account",
            )

        """
        We come here if everything above goes well.
        Here we authenticate the user.
        The authenticate function return None if the credentials do not match 
        or the user account is inactive. However here we can safely raise the exception
        that the credentials did not match as we do all the checks above this point.
        """
        self.user = authenticate(**authenticate_kwargs)
        if self.user is None:
            self.error_messages["no_active_account"] = _("Credentials did not match")
            raise exceptions.AuthenticationFailed(
                self.error_messages["no_active_account"],
                "no_active_account",
            )
        return super().validate(attrs)


class AuthRefreshSerializer(TokenRefreshSerializer):
    def validate(self, attrs):
        token_payload = token_backend.decode(attrs["refresh"])

        try:
            user = get_user_model().objects.get(pk=token_payload["user_id"])
        except get_user_model().DoesNotExist:
            self.error_messages["no_active_account"] = _("Account does not exist")
            raise exceptions.AuthenticationFailed(self.error_messages["no_active_account"], "no_active_account")

        if user.email_address != token_payload["email_address"] or user.username != token_payload["name"]:
            self.error_messages["no_active_account"] = _("Account does not exist")
            raise exceptions.AuthenticationFailed(self.error_messages["no_active_account"], "no_active_account")
        elif not user.is_active:
            self.error_messages["no_active_account"] = _("Account has been deactivated")
            raise exceptions.AuthenticationFailed(self.error_messages["no_active_account"], "no_active_account")

        return super().validate(attrs)
