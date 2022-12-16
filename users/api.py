from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from rest_framework import status, views, permissions
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from users.serializers import *
from users.models import *
from difflib import SequenceMatcher


class CheckUsernameView(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        username = request.data.get("username")
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response(data={"message": "Username available."}, status=status.HTTP_200_OK)
        else:
            return Response(
                data={"message": "Sorry, Username unavailable."},
                status=status.HTTP_409_CONFLICT,
            )


class ChangeUsernameView(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        username = request.data.get("username")
        userId = request.data.get("user_id")

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response(data={"message": "Username available."}, status=status.HTTP_200_OK)
        else:
            if str(user.pk) != userId:
                return Response(
                    data={"message": "Sorry, Username unavailable."},
                    status=status.HTTP_409_CONFLICT,
                )
            else:
                return Response(
                    data={"message": "Retaining Username."},
                    status=status.HTTP_200_OK,
                )


class CheckEmailAddressView(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)

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
                    data={"message": "Sorry, Email Address unavailable."},
                    status=status.HTTP_409_CONFLICT,
                )
        except ValidationError:
            return Response(
                data={"message": "Please enter a valid Email Address format."},
                status=status.HTTP_400_BAD_REQUEST,
            )


class ChangeEmailAddressView(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        email_address = request.data.get("email_address")
        userId = request.data.get("user_id")

        try:
            validate_email(email_address)
            try:
                user = User.objects.get(email_address=email_address)
            except User.DoesNotExist:
                return Response(
                    data={"message": "Email Address Available"},
                    status=status.HTTP_200_OK,
                )
            else:
                if str(user.pk) != userId:
                    return Response(
                        data={"message": "Sorry, Email Address unavailable."},
                        status=status.HTTP_409_CONFLICT,
                    )
                else:
                    return Response(
                        data={"message": "Retaining Email Address."},
                        status=status.HTTP_200_OK,
                    )
        except ValidationError:
            return Response(
                data={"message": "Please enter a valid Email Address format."},
                status=status.HTTP_400_BAD_REQUEST,
            )


class ChangePassword(views.APIView):
    model = User
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self, request, queryset=None):
        user = User.objects.get(id=request)
        return user

    def post(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            request.data["user"] = self.request.user.pk
            serializer = ChangePasswordSerializer(data=request.data)

            if serializer.is_valid():
                user = serializer.data.get("user")
                current_password = serializer.data.get("current_password")
                self.object = self.get_object(user)
                if not self.object.check_password(current_password):
                    return Response(
                        data={"message": "Invalid Current Password."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                self.object.set_password(serializer.data.get("new_password"))
                self.object.save()
                return Response(data={"message": "Password Updated."}, status=status.HTTP_200_OK)

            for error in serializer.errors:
                message = serializer.errors[error]

                return Response(data={"message": message}, status=status.HTTP_400_BAD_REQUEST)


class ResetPassword(views.APIView):
    model = User
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self, request, queryset=None):
        user = User.objects.get(id=request)
        return user

    def post(self, request, *args, **kwargs):
        serializer = ResetPasswordSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.data.get("user")
            self.object = self.get_object(user)

            self.object.set_password(serializer.data.get("new_password"))
            self.object.save()
            return Response(data={"message": "Password Updated."}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordValidation(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)

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


# class UserAccountViewSet(ModelViewSet):
#     queryset = User.objects.all()
#     serializer_class = UserAccountSerializer
#     permission_classes = (permissions.IsAuthenticated,)
#     http_method_names = ["get"]

#     def get_queryset(self):
#         queryset = User.objects.exclude(is_active=False)
#         user = self.request.user.id

#         if user is not None:
#             max_account_limit = settings.filter(property=Property.MAX_USER_ACCOUNT_LIMIT).first().value

#             queryset = (
#                 queryset.prefetch_related(
#                     Prefetch(
#                         "account_user",
#                         queryset=Account.objects.annotate(account_name=Concat(F("first_name"), V(" "), F("last_name")))
#                         .filter(is_deleted=False, account_status=AccountStatus.ACTIVE)
#                         .order_by("id"),
#                     )
#                 )
#                 .annotate(remaining=max_account_limit - Count("account_user"))
#                 .filter(id=user)
#                 .exclude(is_active=False)
#             )

#             return queryset


class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticated,)
    http_method_names = ["get"]

    def get_queryset(self):
        queryset = User.objects.exclude(is_active=False)
        if self.request.user.is_authenticated:
            queryset = queryset.filter(id=self.request.user.pk).exclude(is_active=False)

            return queryset


class UserLogsViewSet(ModelViewSet):
    queryset = UserLogs.objects.all()
    serializer_class = UserLogsSerializer
    permission_classes = (permissions.IsAuthenticated,)
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
    permission_classes = (permissions.IsAuthenticated,)
    http_method_names = ["get"]

    def get_queryset(self):
        queryset = ContentType.objects.all()
        model = self.request.query_params.get("model", None)

        if model is not None:
            queryset = queryset.filter(model=model)

        return queryset
