from rest_framework.routers import DefaultRouter
from django.urls import path
from core.api import (
    CashoutMethodView,
    CreateFranchiseeView,
    FranchiseeListViewSet,
    SettingsViewSet,
    PackagesViewSet,
    ReferralBonusesViewSet,
    LeadershipBonusesViewSet,
    CodeAdminViewSet,
    CodeViewSet,
    ActivitiesViewSet,
    ActivitiesAdminWalletViewSet,
    ActivitiesMemberWalletViewSet,
    CashoutAdminListViewSet,
    CashoutAdminInfoViewSet,
    UpdateCashoutStatusView,
    CashoutMemberInfoViewSet,
    CashoutMemberListViewSet,
    GetEnumTypesView,
    CreatePackageView,
    GetCodeTypesView,
    GenerateCodeView,
    VerifyCodeView,
    UpdateCodeStatusView,
    SummaryMemberFranchiseeAdminView,
    SummaryAdminView,
    SummaryMemberView,
    SummaryActivityAmountAdminView,
    SummaryActivityAmountMemberView,
    SummaryWalletAdminView,
    SummaryWalletMemberView,
    SummaryPVWalletAdminView,
    SummaryPVWalletMemberView,
    RequestCashoutView,
    VerifyFranchiseeCodeView,
    WalletCashoutView,
    WalletComputeTotalView,
    WalletTotalFeeView,
    WalletScheduleView,
    WalletMaxAmountView,
)

router = DefaultRouter()
# Admin
router.register(r"getsettings", SettingsViewSet)
router.register(r"getpackages", PackagesViewSet)
router.register(r"getreferralbonuses", ReferralBonusesViewSet)
router.register(r"getleadershipbonuses", LeadershipBonusesViewSet)
router.register(r"getallwalletsummarylist", ActivitiesAdminWalletViewSet)
router.register(r"getactivities", ActivitiesViewSet)
router.register(r"getcodes", CodeAdminViewSet)
router.register(r"getallcashouts", CashoutAdminListViewSet)
router.register(r"getcashoutadmininfo", CashoutAdminInfoViewSet)
# Members
router.register(r"getaccountcodes", CodeViewSet)
router.register(r"getcashoutinfo", CashoutMemberInfoViewSet)
router.register(r"getcashouts", CashoutMemberListViewSet)
# Wallet Urls
router.register(r"getwalletsummarylist", ActivitiesMemberWalletViewSet)
# Franchisee
router.register(r"getallfranchiseelist", FranchiseeListViewSet)

urlpatterns = [
    path("getenums/", GetEnumTypesView.as_view()),
    path("createpackage/", CreatePackageView.as_view()),
    path("generatecode/", GenerateCodeView.as_view()),
    path("getcodetypes/", GetCodeTypesView.as_view()),
    path("updatecodestatus/", UpdateCodeStatusView.as_view()),
    # Member
    # Admin
    path("getallmembersfranchiseesummaryinfo/", SummaryMemberFranchiseeAdminView.as_view()),
    path("getallactivitysummaryinfo/", SummaryAdminView.as_view()),
    path("getallactivitytotalamount/", SummaryActivityAmountAdminView.as_view()),
    path("getcompanywalletsummary/", SummaryWalletAdminView.as_view()),
    path("getallpvwalletsummary/", SummaryPVWalletAdminView.as_view()),
    path("updatecashoutstatus/", UpdateCashoutStatusView.as_view()),
    # Member
    path("getactivitysummaryinfo/", SummaryMemberView.as_view()),
    path("getactivitytotalamount/", SummaryActivityAmountMemberView.as_view()),
    path("getwalletsummary/", SummaryWalletMemberView.as_view()),
    path("getpvwalletsummary/", SummaryPVWalletMemberView.as_view()),
    # create requests
    path("verifycode/", VerifyCodeView.as_view()),
    path("getcashoutmethods/", CashoutMethodView.as_view()),
    path("getcashoutschedule/", WalletScheduleView.as_view()),
    path("checkwalletcashout/", WalletCashoutView.as_view()),
    path("checkwalletmaxcashout/", WalletMaxAmountView.as_view()),
    path("getcashouttotal/", WalletComputeTotalView.as_view()),
    path("getcashouttotalfee/", WalletTotalFeeView.as_view()),
    path("request/", RequestCashoutView.as_view()),
    # franchisee
    path("verifyfranchisecode/", VerifyFranchiseeCodeView.as_view()),
    path("createfranchisee/", CreateFranchiseeView.as_view()),
]


urlpatterns += router.urls
