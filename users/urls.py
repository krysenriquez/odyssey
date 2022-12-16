from rest_framework.routers import DefaultRouter
from users.api import *
from django.urls import path

router = DefaultRouter()
router.register(r"getuser", UserViewSet)
router.register(r"userlogs", UserLogsViewSet)
router.register(r"contenttype", ContentTypeViewSet)

urlpatterns = [
    path("checkusername/", CheckUsernameView.as_view()),
    path("changeusername/", ChangeUsernameView.as_view()),
    path("checkemailaddress/", CheckEmailAddressView.as_view()),
    path("changeemailaddress/", ChangeEmailAddressView.as_view()),
    path("changepassword/", ChangePassword.as_view()),
    path("resetpassword/", ResetPassword.as_view()),
    path("checkpassword/", PasswordValidation.as_view()),
]

urlpatterns += router.urls
