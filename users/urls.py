from rest_framework.routers import DefaultRouter
from users.api import (
    UserViewSet,
    UserLogsViewSet,
    ContentTypeViewSet,
    CheckUsernameView,
    ChangeUsernameAdminView,
    ChangeEmailAddressAdminView,
    ChangePasswordAdminView,
    ChangeUsernameView,
    CheckEmailAddressView,
    ChangeEmailAddressView,
    ChangePasswordView,
    ResetPasswordView,
    PasswordValidation,
    RetrieveRolePermissionsView,
)
from django.urls import path

router = DefaultRouter()
router.register(r"getuser", UserViewSet)
router.register(r"userlogs", UserLogsViewSet)
router.register(r"contenttype", ContentTypeViewSet)

urlpatterns = [
    path("checkusername/", CheckUsernameView.as_view()),
    path("checkemailaddress/", CheckEmailAddressView.as_view()),
    path("resetpassword/", ResetPasswordView.as_view()),
    path("checkpassword/", PasswordValidation.as_view()),
    path("getpermissions/", RetrieveRolePermissionsView.as_view()),
    # Admin
    path("changeusernameadmin/", ChangeUsernameAdminView.as_view()),
    path("changeemailaddressadmin/", ChangeEmailAddressAdminView.as_view()),
    path("changepasswordadmin/", ChangePasswordAdminView.as_view()),
    # Member
    path("changeusername/", ChangeUsernameView.as_view()),
    path("changeemailaddress/", ChangeEmailAddressView.as_view()),
    path("changepassword/", ChangePasswordView.as_view()),
]

urlpatterns += router.urls
