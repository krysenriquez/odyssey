from django.core.validators import validate_email
from django.template.loader import render_to_string
from django.core.exceptions import ValidationError
from django.db.models import Q, Prefetch, F, Value as V, Count
from django.db.models.functions import Concat
from rest_framework import status, views, permissions
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from difflib import SequenceMatcher
from users.serializers import *
from users.models import *
from vanguard.permissions import IsDeveloperUser, IsAdminUser, IsStaffUser, IsMemberUser
from vanguard.throttle import TenPerMinuteAnonThrottle


class CheckUsernameView(views.APIView):
    permission_classes = []
    throttle_classes = [TenPerMinuteAnonThrottle]

    def post(self, request, *args, **kwargs):
        username = request.data.get("username")
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response(data={"message": "Username available."}, status=status.HTTP_200_OK)
        else:
            return Response(
                data={"message": "Username unavailable."},
                status=status.HTTP_409_CONFLICT,
            )


class CheckEmailAddressView(views.APIView):
    permission_classes = []
    throttle_classes = [TenPerMinuteAnonThrottle]

    def post(self, request, *args, **kwargs):
        email_address = request.data.get("email_address")
        try:
            validate_email(email_address)
            try:
                user = User.objects.get(email_address=email_address)
            except User.DoesNotExist:
                return Response(
                    data={"message": "Email Address available"},
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    data={"message": "Email Address unavailable."},
                    status=status.HTTP_409_CONFLICT,
                )
        except ValidationError:
            return Response(
                data={"message": "Please enter a valid Email Address format."},
                status=status.HTTP_400_BAD_REQUEST,
            )


class ChangeUsernameAdminView(views.APIView):
    permission_classes = [IsDeveloperUser | IsAdminUser | IsStaffUser]

    def post(self, request, *args, **kwargs):
        new_username = request.data.get("username")
        password = request.data.get("admin_password")
        member_user = User.objects.get(user_id=request.data.get("user_id"))
        logged_user = self.request.user

        try:
            user = User.objects.get(username=new_username)
        except User.DoesNotExist:
            if not logged_user.check_password(password):
                return Response(
                    data={"message": "Invalid Admin Password."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            data = {"username": new_username, "can_change_username": False}
            serializer = UserSerializer(member_user, data=data, partial=True)

            if serializer.is_valid():
                serializer.save()
                return Response(data={"message": "Username has been updated"}, status=status.HTTP_200_OK)
            return Response(data={"message": "Unable to update username"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            if user != member_user:
                return Response(
                    data={"message": "Username unavailable."},
                    status=status.HTTP_409_CONFLICT,
                )
            else:
                return Response(
                    data={"message": "Retaining Username."},
                    status=status.HTTP_400_BAD_REQUEST,
                )


class ChangeEmailAddressAdminView(views.APIView):
    permission_classes = [IsDeveloperUser | IsAdminUser | IsStaffUser]

    def post(self, request, *args, **kwargs):
        email_address = request.data.get("email_address")
        password = request.data.get("admin_password")
        member_user = User.objects.get(user_id=request.data.get("user_id"))
        logged_user = self.request.user

        try:
            validate_email(email_address)
            try:
                user = User.objects.get(email_address=email_address)
            except User.DoesNotExist:
                if not logged_user.check_password(password):
                    return Response(
                        data={"message": "Invalid Admin Password."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                data = {"email_address": email_address, "can_change_email_address": False}
                serializer = UserSerializer(member_user, data=data, partial=True)

                if serializer.is_valid():
                    serializer.save()
                    return Response(
                        data={"message": "Email Address has been updated"},
                        status=status.HTTP_200_OK,
                    )
                return Response(data={"message": "Unable to update Email Address"}, status=status.HTTP_400_BAD_REQUEST)
            else:
                if user != member_user:
                    return Response(
                        data={"message": "Email Address unavailable."},
                        status=status.HTTP_409_CONFLICT,
                    )
                else:
                    return Response(
                        data={"message": "Retaining Email Address."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
        except ValidationError:
            return Response(
                data={"message": "Please enter a valid Email Address format."},
                status=status.HTTP_400_BAD_REQUEST,
            )


class ChangePasswordAdminView(views.APIView):
    model = User
    permission_classes = [IsDeveloperUser | IsAdminUser | IsStaffUser]

    def post(self, request, *args, **kwargs):
        new_password = request.data.get("new_password")
        password = request.data.get("admin_password")
        member_user = User.objects.get(user_id=request.data.get("user_id"))
        logged_user = self.request.user

        if not logged_user.check_password(password):
            return Response(
                data={"message": "Invalid Admin Password."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        member_user.set_password(new_password)
        member_user.can_change_password = False
        member_user.save()

        return Response(data={"message": "Password Updated."}, status=status.HTTP_200_OK)


class ChangeUsernameView(views.APIView):
    permission_classes = [IsDeveloperUser | IsAdminUser | IsStaffUser | IsMemberUser]

    def post(self, request, *args, **kwargs):
        new_username = request.data.get("username")
        password = request.data.get("confirm_password")
        logged_user = self.request.user
        try:
            user = User.objects.get(username=new_username)
        except User.DoesNotExist:
            if not logged_user.check_password(password):
                return Response(
                    data={"message": "Invalid Current Password."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            data = {"username": new_username, "can_change_username": False}
            serializer = UserSerializer(logged_user, data=data, partial=True)
            if serializer.is_valid():
                print(serializer)
                serializer.save()
                return Response(data={"message": "Username has been updated"}, status=status.HTTP_200_OK)
            return Response(data={"message": "Unable to update username"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            if user != logged_user:
                return Response(
                    data={"message": "Username unavailable."},
                    status=status.HTTP_409_CONFLICT,
                )
            else:
                return Response(
                    data={"message": "Retaining Username."},
                    status=status.HTTP_400_BAD_REQUEST,
                )


class ChangeEmailAddressView(views.APIView):
    permission_classes = [IsDeveloperUser | IsAdminUser | IsStaffUser | IsMemberUser]

    def post(self, request, *args, **kwargs):
        email_address = request.data.get("email_address")
        password = request.data.get("confirm_password")
        logged_user = self.request.user
        try:
            validate_email(email_address)
            try:
                user = User.objects.get(email_address=email_address)
            except User.DoesNotExist:
                if not logged_user.check_password(password):
                    return Response(
                        data={"message": "Invalid Current Password."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                data = {"email_address": email_address, "can_change_email_address": False}
                serializer = UserSerializer(logged_user, data=data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return Response(
                        data={"message": "Email Address has been updated"},
                        status=status.HTTP_200_OK,
                    )
                return Response(data={"message": "Unable to update Email Address"}, status=status.HTTP_400_BAD_REQUEST)
            else:
                if user != logged_user:
                    return Response(
                        data={"message": "Email Address unavailable."},
                        status=status.HTTP_409_CONFLICT,
                    )
                else:
                    return Response(
                        data={"message": "Retaining Email Address."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
        except ValidationError:
            return Response(
                data={"message": "Please enter a valid Email Address format."},
                status=status.HTTP_400_BAD_REQUEST,
            )


class ChangePasswordView(views.APIView):
    model = User
    permission_classes = [IsDeveloperUser | IsAdminUser | IsStaffUser | IsMemberUser]

    def post(self, request, *args, **kwargs):
        new_password = request.data.get("new_password")
        password = request.data.get("current_password")
        logged_user = self.request.user

        if not logged_user.check_password(password):
            return Response(
                data={"message": "Invalid Current Password."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        logged_user.set_password(new_password)
        logged_user.can_change_password = False
        logged_user.save()

        return Response(data={"message": "Password Updated."}, status=status.HTTP_200_OK)


class ResetPasswordView(views.APIView):
    model = User
    permission_classes = [IsDeveloperUser | IsAdminUser | IsStaffUser | IsMemberUser]

    def post(self, request, *args, **kwargs):
        new_password = request.data.get("new_password")
        refresh_token = self.request.data.get("refresh")
        logged_user = self.request.user
        logged_user.set_password(new_password)
        logged_user.save()
        token = RefreshToken(token=refresh_token)
        token.blacklist()
        return Response(data={"message": "Password Updated."}, status=status.HTTP_200_OK)


class PasswordValidation(views.APIView):
    permission_classes = [IsDeveloperUser | IsAdminUser | IsStaffUser | IsMemberUser]

    def post(self, request, *args, **kwargs):
        username = request.data.get("username")
        emailAddress = request.data.get("email_address")
        password = request.data.get("password")
        max_similarity = 0.7
        if SequenceMatcher(password.lower(), username.lower()).quick_ratio() > max_similarity:
            return Response(
                data={"message": "The password is too similar to the username.", "similar": True},
                status=status.HTTP_403_FORBIDDEN,
            )
        if SequenceMatcher(password.lower(), emailAddress.lower()).quick_ratio() > max_similarity:
            return Response(
                data={"message": "The password is too similar to the email.", "similar": True},
                status=status.HTTP_403_FORBIDDEN,
            )


class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsDeveloperUser | IsAdminUser | IsStaffUser | IsMemberUser]
    http_method_names = ["get"]

    def get_queryset(self):
        queryset = User.objects.exclude(is_active=False)
        if self.request.user.is_authenticated:
            queryset = queryset.filter(id=self.request.user.pk).exclude(is_active=False)

            return queryset


class UserLogsViewSet(ModelViewSet):
    queryset = UserLogs.objects.all()
    serializer_class = UserLogsSerializer
    permission_classes = [IsDeveloperUser | IsAdminUser | IsStaffUser | IsMemberUser]
    http_method_names = ["get"]

    def get_queryset(self):
        queryset = UserLogs.objects.order_by("-id")
        content_type = self.request.query_params.get("content_type", None)
        object_id = self.request.query_params.get("object_id", None)
        user = self.request.query_params.get("user", None)

        if content_type is not None:
            queryset = queryset.filter(content_type=content_type, object_id=object_id)

        if user is not None:
            queryset = queryset.filter(user=user)

        return queryset


class ContentTypeViewSet(ModelViewSet):
    queryset = ContentType.objects.all()
    serializer_class = ContentTypeSerializer
    permission_classes = [IsDeveloperUser | IsAdminUser | IsStaffUser | IsMemberUser]
    http_method_names = ["get"]

    def get_queryset(self):
        queryset = ContentType.objects.all()
        model = self.request.query_params.get("model", None)

        if model is not None:
            queryset = queryset.filter(model=model)

        return queryset


class RetrieveRolePermissionsView(views.APIView):
    permission_classes = [IsDeveloperUser | IsAdminUser | IsStaffUser]

    def post(self, request, *args, **kwargs):
        role_permission = RolePermissions.objects.filter(user_type=request.user.user_type)
        serializer = RolePermissionsSerializer(role_permission, many=True)
        return Response(
            data={"permissions": serializer.data},
            status=status.HTTP_200_OK,
        )
