from rest_framework.routers import DefaultRouter
from accounts.api import (
    AccountProfileViewSet,
    AccountListViewSet,
    AccountReferralsViewSet,
    BinaryAccountProfileViewSet,
    GenealogyAccountAdminViewSet,
    GenealogyAccountMemberViewSet,
    TopAccountWalletViewSet,
    CreateAccountView,
    VerifyAccountView,
    VerifySponsorCodeView,
)
from django.urls import path

router = DefaultRouter()
router.register(r"getprofile", AccountProfileViewSet)
router.register(r"getmembers", AccountListViewSet)
router.register(r"getreferrals", AccountReferralsViewSet)
router.register(r"getbinaryprofile", BinaryAccountProfileViewSet)
router.register(r"getgenealogyadmin", GenealogyAccountAdminViewSet)
router.register(r"getgenealogy", GenealogyAccountMemberViewSet)
router.register(r"gettopearners", TopAccountWalletViewSet)

urlpatterns = [
    path("create/", CreateAccountView.as_view()),
    path("verifyaccount/", VerifyAccountView.as_view()),
    path("verifysponsorcode/", VerifySponsorCodeView.as_view()),
]

urlpatterns += router.urls
