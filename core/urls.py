from rest_framework.routers import DefaultRouter
from django.urls import path
from core.api import (
    SettingsViewSet,
    PackagesViewSet,
    ReferralBonusesViewSet,
    LeadershipBonusesViewSet,
    CodeViewSet,
    ActivitiesViewSet,
    ActivitiesAdminWalletViewSet,
    ActivitiesMemberWalletViewSet,
    GetCodeTypesView,
    GenerateCodeView,
    SummaryAdminView,
    SummaryMemberView,
    SummaryActivityAmountAdminView,
    SummaryActivityAmountMemberView,
    SummaryWalletAdminView,
    SummaryWalletMemberView,
    SummaryPVWalletAdminView,
    SummaryPVWalletMemberView,
)

router = DefaultRouter()
router.register(r"getsettings", SettingsViewSet)
router.register(r"getpackages", PackagesViewSet)
router.register(r"getreferralbonuses", ReferralBonusesViewSet)
router.register(r"getleadershipbonuses", LeadershipBonusesViewSet)
router.register(r"getcodes", CodeViewSet)
router.register(r"getactivities", ActivitiesViewSet)
# Wallet Urls
router.register(r"getallwalletsummary", ActivitiesAdminWalletViewSet)
router.register(r"getwalletsummary", ActivitiesMemberWalletViewSet)


urlpatterns = [
    path("getcodetypes/", GetCodeTypesView.as_view()),
    path("generatecode/", GenerateCodeView.as_view()),
    path("getallactivitysummaryinfo/", SummaryAdminView.as_view()),
    path("getactivitysummaryinfo/", SummaryMemberView.as_view()),
    path("getallactivitytotalamount/", SummaryActivityAmountAdminView.as_view()),
    path("getactivitytotalamount/", SummaryActivityAmountMemberView.as_view()),
    path("getallwalletsummary/", SummaryWalletAdminView.as_view()),
    path("getawalletsummary/", SummaryWalletMemberView.as_view()),
    path("getallpvwalletsummary/", SummaryPVWalletAdminView.as_view()),
    path("getpvwalletsummary/", SummaryPVWalletMemberView.as_view()),
]


urlpatterns += router.urls
