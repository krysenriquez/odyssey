from rest_framework import status, views, permissions
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from django.db.models import Sum, F, Q, Case, When, DecimalField
from django.db.models.functions import Coalesce
from accounts.models import Account
from vanguard.permissions import IsDeveloperUser, IsAdminUser, IsStaffUser, IsMemberUser
from core.enums import ActivityType, CodeStatus, CodeType, WalletType
from core.models import (
    Setting,
    Package,
    ReferralBonus,
    LeadershipBonus,
    Code,
    Activity,
)
from core.serializers import (
    SettingsSerializer,
    PackagesSerializer,
    ReferralBonusesSerializer,
    LeadershipBonusesSerializer,
    CodesSerializer,
    ActivitiesSerializer,
    GenerateCodeSerializer,
)

# ModelViewset
class SettingsViewSet(ModelViewSet):
    queryset = Setting.objects.all()
    serializer_class = SettingsSerializer
    permission_classes = [IsDeveloperUser | IsAdminUser | IsStaffUser]
    http_method_names = ["get"]

    def get_queryset(self):
        queryset = Setting.objects.all()

        return queryset


class PackagesViewSet(ModelViewSet):
    queryset = Package.objects.all()
    serializer_class = PackagesSerializer
    permission_classes = [IsDeveloperUser | IsAdminUser | IsStaffUser]
    http_method_names = ["get"]

    def get_queryset(self):
        queryset = Package.objects.all()

        return queryset


class ReferralBonusesViewSet(ModelViewSet):
    queryset = ReferralBonus.objects.all()
    serializer_class = ReferralBonusesSerializer
    permission_classes = [IsDeveloperUser | IsAdminUser | IsStaffUser]
    http_method_names = ["get"]

    def get_queryset(self):
        queryset = ReferralBonus.objects.all()

        return queryset


class LeadershipBonusesViewSet(ModelViewSet):
    queryset = LeadershipBonus.objects.all()
    serializer_class = LeadershipBonusesSerializer
    permission_classes = [IsDeveloperUser | IsAdminUser | IsStaffUser]
    http_method_names = ["get"]

    def get_queryset(self):
        queryset = LeadershipBonus.objects.all()

        return queryset


class CodeViewSet(ModelViewSet):
    queryset = Code.objects.all()
    serializer_class = CodesSerializer
    permission_classes = [IsDeveloperUser | IsAdminUser | IsStaffUser]
    http_method_names = ["get"]

    def get_queryset(self):
        queryset = Code.objects.exclude(is_deleted=True).order_by("-modified")

        return queryset


class ActivitiesViewSet(ModelViewSet):
    queryset = Activity.objects.all()
    serializer_class = ActivitiesSerializer
    permission_classes = [IsDeveloperUser | IsAdminUser | IsStaffUser]
    http_method_names = ["get"]

    def get_queryset(self):
        activity_type = self.request.query_params.get("activity_type", None)
        account_id = self.request.query_params.get("account_id", None)
        if activity_type is not None:
            queryset = (
                Activity.objects.exclude(is_deleted=True)
                .filter(activity_type=activity_type)
                .annotate(
                    amount=Case(
                        When(
                            Q(activity_type=ActivityType.CASHOUT),
                            then=0 - (Sum(F("activity_amount"))),
                        ),
                        When(
                            ~Q(activity_type=ActivityType.CASHOUT),
                            then=Sum(F("activity_amount")),
                        ),
                    )
                )
                .order_by("-modified")
            )
            if account_id is not None:
                queryset = queryset.filter(account__account_id=account_id)

            return queryset


# Wallets ViewSet
class ActivitiesAdminWalletViewSet(ModelViewSet):
    queryset = Activity.objects.all()
    serializer_class = ActivitiesSerializer
    permission_classes = [IsDeveloperUser | IsAdminUser | IsStaffUser]
    http_method_names = ["get"]

    def get_queryset(self):
        queryset = Activity.objects.exclude(is_deleted=True)
        wallet = self.request.query_params.get("wallet", None)
        if wallet is not None:
            account_id = self.request.query_params.get("account_id", None)
            if account_id is not None:
                return (
                    queryset.filter(account__account_id=account_id, wallet=wallet)
                    .annotate(
                        amount=Case(
                            When(
                                Q(activity_type=ActivityType.CASHOUT),
                                then=0 - (Sum(F("activity_amount"))),
                            ),
                            When(
                                ~Q(activity_type=ActivityType.CASHOUT),
                                then=Sum(F("activity_amount")),
                            ),
                        )
                    )
                    .order_by("-modified")
                )
            else:
                return (
                    queryset.filter(wallet=wallet)
                    .annotate(
                        amount=Case(
                            When(
                                Q(activity_type=ActivityType.CASHOUT),
                                then=0 - Sum(F("activity_amount")),
                            ),
                            When(
                                ~Q(activity_type=ActivityType.CASHOUT),
                                then=Sum(F("activity_amount")),
                            ),
                        )
                    )
                    .order_by("-modified")
                )


# TODO: Verify after Member Creation
class ActivitiesMemberWalletViewSet(ModelViewSet):
    queryset = Activity.objects.all()
    serializer_class = ActivitiesSerializer
    permission_classes = [IsDeveloperUser | IsAdminUser | IsStaffUser | IsMemberUser]
    http_method_names = ["get"]

    def get_queryset(self):
        queryset = Activity.objects.exclude(is_deleted=True)
        wallet = self.request.query_params.get("wallet", None)
        if wallet is not None:
            account_id = self.request.query_params.get("account_id", None)
            if account_id is not None:
                account = Account.objects.get(account_id=account_id)
                user_accounts = self.request.user.get_all_user_accounts()
                if account in user_accounts:
                    return (
                        queryset.filter(account__account_id=account_id, wallet=wallet)
                        .annotate(
                            amount=Case(
                                When(
                                    Q(activity_type=ActivityType.CASHOUT),
                                    then=0 - (Sum(F("activity_amount"))),
                                ),
                                When(
                                    ~Q(activity_type=ActivityType.CASHOUT),
                                    then=Sum(F("activity_amount")),
                                ),
                            )
                        )
                        .order_by("-modified")
                    )


# Views POST
class GetCodeTypesView(views.APIView):
    permission_classes = [IsDeveloperUser | IsAdminUser | IsStaffUser]

    def post(self, request, *args, **kwargs):
        status_arr = []
        for code in CodeType:
            status_arr.append(code)

        if status_arr:
            return Response(
                data={"status": status_arr},
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                data={"message": "No Code Types available."},
                status=status.HTTP_404_NOT_FOUND,
            )


class GenerateCodeView(views.APIView):
    permission_classes = [IsDeveloperUser | IsAdminUser | IsStaffUser]

    def post(self, request, *args, **kwargs):
        # request.data["owner"] = request.data.get("owner_id").lstrip("0")
        request.data["created_by"] = request.user.pk
        serializer = GenerateCodeSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(data={"message": "Code generated."}, status=status.HTTP_201_CREATED)
        else:
            return Response(
                data={"message": "Unable to generate code."},
                status=status.HTTP_404_NOT_FOUND,
            )


class SummaryAdminView(views.APIView):
    permission_classes = [IsDeveloperUser | IsAdminUser | IsStaffUser]

    def post(self, request, *args, **kwargs):
        data = []
        entry_count = Activity.objects.filter(activity_type=ActivityType.ENTRY).count()
        data.append({"activity": ActivityType.ENTRY, "summary": entry_count})

        referrals_count = Activity.objects.filter(activity_type=ActivityType.DIRECT_REFERRAL).count()
        data.append({"activity": ActivityType.DIRECT_REFERRAL, "summary": referrals_count})

        sales_match_count = Activity.objects.filter(activity_type=ActivityType.SALES_MATCH).count()
        data.append({"activity": ActivityType.SALES_MATCH, "summary": sales_match_count})

        flush_out_count = Activity.objects.filter(
            activity_type=ActivityType.FLUSH_OUT_PENALTY, wallet=WalletType.PV_LEFT_WALLET
        ).count()
        data.append({"activity": ActivityType.FLUSH_OUT_PENALTY, "summary": flush_out_count})

        return Response(
            data=data,
            status=status.HTTP_200_OK,
        )


class SummaryMemberView(views.APIView):
    permission_classes = [IsDeveloperUser | IsAdminUser | IsStaffUser | IsMemberUser]

    def post(self, request, *args, **kwargs):
        account_id = request.data.get("account_id")
        data = []

        referrals_count = Activity.objects.filter(
            account__account_id=account_id, activity_type=ActivityType.DIRECT_REFERRAL
        ).count()
        data.append({"activity": ActivityType.DIRECT_REFERRAL, "summary": referrals_count})

        sales_match_count = Activity.objects.filter(
            account__account_id=account_id, activity_type=ActivityType.SALES_MATCH
        ).count()
        data.append({"activity": ActivityType.SALES_MATCH, "summary": sales_match_count})

        flush_out_count = Activity.objects.filter(
            account__account_id=account_id,
            activity_type=ActivityType.FLUSH_OUT_PENALTY,
            wallet=WalletType.PV_LEFT_WALLET,
        ).count()
        data.append({"activity": ActivityType.FLUSH_OUT_PENALTY, "summary": flush_out_count})

        return Response(
            data=data,
            status=status.HTTP_200_OK,
        )


class SummaryActivityAmountAdminView(views.APIView):
    permission_classes = [IsDeveloperUser | IsAdminUser | IsStaffUser]

    def post(self, request, *args, **kwargs):
        data = []
        for activity in ActivityType:
            activities = (
                Activity.objects.filter(activity_type=activity)
                .values("activity_type")
                .annotate(activity_total=Sum(F("activity_amount")))
                .order_by("-activity_total")
            )

            wallet_total = activities.aggregate(
                total=Coalesce(Sum("activity_total"), 0, output_field=DecimalField())
            ).get("total")

            data.append(
                {
                    "activity": activity,
                    "total": wallet_total,
                }
            )

        return Response(
            data=data,
            status=status.HTTP_200_OK,
        )


class SummaryActivityAmountMemberView(views.APIView):
    permission_classes = [IsDeveloperUser | IsAdminUser | IsStaffUser | IsMemberUser]

    def post(self, request, *args, **kwargs):
        account_id = request.data.get("account_id")
        data = []
        ActivityFilter = [
            ActivityType.ENTRY,
            ActivityType.PAYOUT,
            ActivityType.COMPANY_TAX,
            ActivityType.DOWNLINE_ENTRY,
        ]
        for activity in ActivityType:
            if activity not in ActivityFilter:
                activities = (
                    Activity.objects.filter(account__account_id=account_id, activity_type=activity)
                    .values("activity_type")
                    .annotate(activity_total=Sum(F("activity_amount")))
                    .order_by("-activity_total")
                )

                wallet_total = activities.aggregate(
                    total=Coalesce(Sum("activity_total"), 0, output_field=DecimalField())
                ).get("total")

                data.append(
                    {
                        "activity": activity,
                        "total": wallet_total,
                    }
                )

        return Response(
            data=data,
            status=status.HTTP_200_OK,
        )


class SummaryWalletAdminView(views.APIView):
    permission_classes = [IsDeveloperUser | IsAdminUser | IsStaffUser]

    def post(self, request, *args, **kwargs):
        data = []
        WalletFilter = []
        for wallet in WalletType:
            if wallet not in WalletFilter:
                activities = (
                    Activity.objects.filter(wallet=wallet)
                    .values("activity_type")
                    .annotate(activity_total=Sum(F("activity_amount")))
                    .order_by("-activity_total")
                )
                wallet_total = activities.aggregate(
                    total=Coalesce(Sum("activity_total"), 0, output_field=DecimalField())
                ).get("total")
                data.append(
                    {
                        "wallet": wallet,
                        "total": wallet_total,
                    }
                )

        return Response(
            data=data,
            status=status.HTTP_200_OK,
        )


class SummaryWalletMemberView(views.APIView):
    permission_classes = [IsDeveloperUser | IsAdminUser | IsStaffUser | IsMemberUser]

    def post(self, request, *args, **kwargs):
        account_id = request.data.get("account_id")
        data = []
        WalletFilter = [
            WalletType.C_WALLET,
            WalletType.PV_LEFT_WALLET,
            WalletType.PV_RIGHT_WALLET,
            WalletType.PV_TOTAL_WALLET,
        ]
        for wallet in WalletType:
            if wallet not in WalletFilter:
                activities = (
                    Activity.objects.filter(account__account_id=account_id, wallet=wallet)
                    .values("activity_type")
                    .annotate(activity_total=Sum(F("activity_amount")))
                    .order_by("-activity_total")
                )
                wallet_total = activities.aggregate(
                    total=Coalesce(Sum("activity_total"), 0, output_field=DecimalField())
                ).get("total")
                data.append(
                    {
                        "wallet": wallet,
                        "total": wallet_total,
                    }
                )

        return Response(
            data=data,
            status=status.HTTP_200_OK,
        )


class SummaryPVWalletAdminView(views.APIView):
    permission_classes = [IsDeveloperUser | IsAdminUser | IsStaffUser | IsMemberUser]

    def post(self, request, *args, **kwargs):
        data = []
        WalletFilter = [
            WalletType.C_WALLET,
            WalletType.B_WALLET,
            WalletType.F_WALLET,
        ]
        for wallet in WalletType:
            if wallet not in WalletFilter:
                activities = (
                    Activity.objects.filter(wallet=wallet)
                    .values("activity_type")
                    .annotate(activity_total=Sum(F("activity_amount")))
                    .order_by("-activity_total")
                )
                wallet_total = activities.aggregate(
                    total=Coalesce(Sum("activity_total"), 0, output_field=DecimalField())
                ).get("total")
                data.append(
                    {
                        "wallet": wallet,
                        "total": wallet_total,
                    }
                )

        return Response(
            data=data,
            status=status.HTTP_200_OK,
        )


class SummaryPVWalletMemberView(views.APIView):
    permission_classes = [IsDeveloperUser | IsAdminUser | IsStaffUser | IsMemberUser]

    def post(self, request, *args, **kwargs):
        account_id = request.data.get("account_id")
        data = []
        WalletFilter = [
            WalletType.C_WALLET,
            WalletType.B_WALLET,
            WalletType.F_WALLET,
        ]
        for wallet in WalletType:
            if wallet not in WalletFilter:
                activities = (
                    Activity.objects.filter(account__account_id=account_id, wallet=wallet)
                    .values("activity_type")
                    .annotate(activity_total=Sum(F("activity_amount")))
                    .order_by("-activity_total")
                )
                wallet_total = activities.aggregate(
                    total=Coalesce(Sum("activity_total"), 0, output_field=DecimalField())
                ).get("total")
                data.append(
                    {
                        "wallet": wallet,
                        "total": wallet_total,
                    }
                )

        return Response(
            data=data,
            status=status.HTTP_200_OK,
        )
