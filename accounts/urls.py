from rest_framework.routers import DefaultRouter
from accounts.api import (
    AccountCashoutMethodsViewSet,
    UserAccountAvatarViewSet,
    UserAccountViewSet,
    AccountProfileViewSet,
    AccountListViewSet,
    AccountReferralsViewSet,
    BinaryAccountProfileViewSet,
    GenealogyAccountAdminViewSet,
    GenealogyAccountMemberViewSet,
    TopAccountWalletViewSet,
    CreateAccountView,
    VerifyAccountView,
    VerifySponsorAccountNumberView,
    VerifyParentAccountNumberView,
    VerifyParentSideView,
    VerifyExtremeSide,
    VerifyAccountName,
    UpgradeAccountView,
    VerifyCreateAccountLinkView,
    UpdateUserStatusView,
    UpdateAccountAdminView,
    UpdateAccountView,
    TestCreateView,
)
from django.urls import path

router = DefaultRouter()
# Admin
router.register(r"gettopearners", TopAccountWalletViewSet)
router.register(r"getreferrals", AccountReferralsViewSet)
router.register(r"getmembers", AccountListViewSet)
router.register(r"getgenealogyadmin", GenealogyAccountAdminViewSet)
router.register(r"getmemberuser", UserAccountViewSet)

# Member
router.register(r"getprofile", AccountProfileViewSet)
router.register(r"getaccount", UserAccountAvatarViewSet)
router.register(r"getgenealogy", GenealogyAccountMemberViewSet)
router.register(r"getaccountcashoutmethods", AccountCashoutMethodsViewSet)
router.register(r"getbinaryprofile", BinaryAccountProfileViewSet)

urlpatterns = [
    path("create/", CreateAccountView.as_view()),
    path("verifyaccount/", VerifyAccountView.as_view()),
    path("verifysponsoraccountnumber/", VerifySponsorAccountNumberView.as_view()),
    path("verifyparentaccountnumber/", VerifyParentAccountNumberView.as_view()),
    path("verifyparentside/", VerifyParentSideView.as_view()),
    path("verifyaccountname/", VerifyAccountName.as_view()),
    path("verifyextremeside/", VerifyExtremeSide.as_view()),
    path("upgrade/", UpgradeAccountView.as_view()),
    path("verify/", VerifyCreateAccountLinkView.as_view()),
    path("updateuserstatus/", UpdateUserStatusView.as_view()),
    path("updateprofileadmin/", UpdateAccountAdminView.as_view()),
    path("updateprofile/", UpdateAccountView.as_view()),
    path("test/", TestCreateView.as_view()),
]

urlpatterns += router.urls
