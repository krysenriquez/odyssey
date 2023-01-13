from rest_framework import status, views, permissions
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Sum, F, Q, Case, When, DecimalField
from django.db.models.functions import Coalesce
from accounts.models import Account
from core.services import (
    check_if_has_cashout_today,
    check_if_has_pending_cashout,
    comp_plan,
    compute_cashout_total,
    create_company_earning_activity,
    find_total_sales_match_points_today,
    get_all_enums,
    get_cashout_total_tax,
    compute_minimum_cashout_amount,
    get_setting,
    get_wallet_can_cashout,
    get_wallet_cashout_schedule,
    process_create_cashout_request,
    create_payout_activity,
    process_create_franchisee_request,
    process_save_cashout_status,
    update_code_status,
    verify_code_details,
)
from vanguard.permissions import IsDeveloperUser, IsAdminUser, IsStaffUser, IsMemberUser
from vanguard.throttle import FivePerMinuteAnonThrottle
from core.enums import ActivityStatus, ActivityType, CashoutMethod, CodeStatus, CodeType, WalletType, Settings
from core.models import (
    Franchisee,
    Setting,
    Package,
    ReferralBonus,
    LeadershipBonus,
    Code,
    Activity,
)
from core.serializers import (
    ActivityCashoutInfoSerializer,
    ActivityCashoutListSerializer,
    CreateActivitiesSerializer,
    CreateFranchiseeSerializer,
    FranchiseeListSerializer,
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
        id = self.request.query_params.get("id", None)
        queryset = Setting.objects.all()
        if id is not None:
            queryset = Setting.objects.filter(id=id)

        return queryset


class PackagesViewSet(ModelViewSet):
    queryset = Package.objects.all()
    serializer_class = PackagesSerializer
    permission_classes = [IsDeveloperUser | IsAdminUser | IsStaffUser]
    http_method_names = ["get"]

    def get_queryset(self):
        queryset = Package.objects.all().order_by("package_amount")

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


class CodeAdminViewSet(ModelViewSet):
    queryset = Code.objects.all()
    serializer_class = CodesSerializer
    permission_classes = [IsDeveloperUser | IsAdminUser | IsStaffUser]
    http_method_names = ["get"]

    def get_queryset(self):
        queryset = Code.objects.exclude(is_deleted=True).order_by("-created")

        status = self.request.query_params.get("status", None)
        if status:
            return queryset.filter(status=status)

        is_owned = self.request.query_params.get("is_owned", None)
        if is_owned:
            return queryset.filter(owner__is_null=False)

        code_type = self.request.query_params.get("code_type", None)
        if code_type:
            return queryset.filter(code_type=code_type)

        return queryset


class CodeViewSet(ModelViewSet):
    queryset = Code.objects.all()
    serializer_class = CodesSerializer
    permission_classes = [IsDeveloperUser | IsAdminUser | IsStaffUser | IsMemberUser]
    http_method_names = ["get"]

    def get_queryset(self):
        account_id = self.request.query_params.get("account_id", None)
        if account_id is not None:
            queryset = Code.objects.exclude(is_deleted=True).filter(owner__account_id=account_id).order_by("status")

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
                Activity.objects.exclude(is_deleted=True).filter(activity_type=activity_type).order_by("-modified")
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
                                Q(activity_type=ActivityType.CASHOUT) & Q(status=ActivityStatus.RELEASED),
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


class ActivitiesMemberWalletViewSet(ModelViewSet):
    queryset = Activity.objects.all()
    serializer_class = ActivitiesSerializer
    permission_classes = [IsDeveloperUser | IsAdminUser | IsStaffUser | IsMemberUser]
    http_method_names = ["get"]

    def get_queryset(self):
        account_id = self.request.query_params.get("account_id", None)
        wallet = self.request.query_params.get("wallet", None)
        if account_id is not None and wallet is not None and wallet is not WalletType.C_WALLET:
            queryset = (
                Activity.objects.filter(account__account_id=account_id, wallet=wallet)
                .annotate(
                    amount=Case(
                        When(
                            Q(activity_type=ActivityType.CASHOUT) & ~Q(status=ActivityStatus.DENIED),
                            then=0 - (Sum(F("activity_amount"))),
                        ),
                        When(
                            ~Q(activity_type=ActivityType.CASHOUT),
                            then=Sum(F("activity_amount")),
                        ),
                    )
                )
                .order_by("-modified")
                .exclude(is_deleted=True)
            )
            return queryset


class CashoutAdminListViewSet(ModelViewSet):
    queryset = Activity.objects.all()
    serializer_class = ActivityCashoutListSerializer
    permission_classes = [IsDeveloperUser | IsAdminUser | IsStaffUser]
    http_method_names = ["get"]

    def get_queryset(self):
        queryset = Activity.objects.filter(activity_type=ActivityType.CASHOUT).exclude(is_deleted=True)

        return queryset


class CashoutAdminInfoViewSet(ModelViewSet):
    queryset = Activity.objects.all()
    serializer_class = ActivityCashoutInfoSerializer
    permission_classes = [IsDeveloperUser | IsAdminUser | IsStaffUser]
    http_method_names = ["get"]

    def get_queryset(self):
        activity_number = self.request.query_params.get("activity_number", None)
        if activity_number is not None:
            queryset = Activity.objects.filter(activity_type=ActivityType.CASHOUT, id=activity_number).exclude(
                is_deleted=True
            )

            return queryset


class CashoutMemberInfoViewSet(ModelViewSet):
    queryset = Activity.objects.all()
    serializer_class = ActivityCashoutInfoSerializer
    permission_classes = [IsDeveloperUser | IsAdminUser | IsStaffUser | IsMemberUser]
    http_method_names = ["get"]

    def get_queryset(self):
        account_id = self.request.query_params.get("account_id", None)
        activity_number = self.request.query_params.get("activity_number", None)
        if account_id is not None and activity_number is not None:
            queryset = Activity.objects.filter(
                activity_type=ActivityType.CASHOUT, account__account_id=account_id, id=activity_number
            ).exclude(is_deleted=True)

            return queryset


class CashoutMemberListViewSet(ModelViewSet):
    queryset = Activity.objects.all()
    serializer_class = ActivityCashoutListSerializer
    permission_classes = [IsDeveloperUser | IsAdminUser | IsStaffUser | IsMemberUser]
    http_method_names = ["get"]

    def get_queryset(self):
        account_id = self.request.query_params.get("account_id", None)
        if account_id is not None:
            queryset = Activity.objects.filter(
                activity_type=ActivityType.CASHOUT, account__account_id=account_id
            ).exclude(is_deleted=True)

            return queryset


# Views POST
class CreatePackageView(views.APIView):
    permission_classes = [IsDeveloperUser | IsAdminUser | IsStaffUser]

    def post(self, request, *args, **kwargs):
        request.data["created_by"] = request.user.pk
        serializer = PackagesSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(data={"message": "Package generated."}, status=status.HTTP_201_CREATED)
        else:
            return Response(
                data={"message": "Unable to generate Package."},
                status=status.HTTP_404_NOT_FOUND,
            )


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
        quantity = request.data["quantity"]
        if quantity:
            for i in range(int(quantity)):
                request.data["created_by"] = request.user.pk
                request.data["status"] = CodeStatus.ACTIVE
                serializer = GenerateCodeSerializer(data=request.data)

                if serializer.is_valid():
                    serializer.save()
                else:
                    return Response(
                        data={"message": "Unable to generate code."},
                        status=status.HTTP_404_NOT_FOUND,
                    )
            else:
                return Response(data={"message": "Code generated."}, status=status.HTTP_201_CREATED)


class VerifyCodeView(views.APIView):
    permission_classes = []
    throttle_classes = [FivePerMinuteAnonThrottle]

    def post(self, request, *args, **kwargs):
        is_verified, message, activation_code, package = verify_code_details(request)

        if not is_verified:
            return Response(
                data={"message": message},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if package.is_franchise:
            return Response(
                data={"message": "Code not valid."},
                status=status.HTTP_404_NOT_FOUND,
            )

        referrral_bonus = ReferralBonus.objects.filter(package_referrer=package)
        leadership_bonus = LeadershipBonus.objects.filter(package=package)
        flushout_limit = "{:,.2f}".format(package.flush_out_limit)
        flushout_limit_currency = "{:,.2f}".format(
            package.flush_out_limit * get_setting(Settings.POINT_VALUE_CONVERSION)
        )
        package_details = [
            {"Pairing": package.has_pairing},
            {"Up to %s PV / ₱%s Flushout Limit" % (flushout_limit, flushout_limit_currency): package.has_pairing},
            {"Referral Bonus": referrral_bonus.exists()},
            {"Leadership Bonus": leadership_bonus.exists()},
            {"BCO": package.is_bco},
        ]
        return Response(
            data={
                "message": "Code valid.",
                "package": {
                    "codeType": activation_code.code_type,
                    "packagId": package.pk,
                    "packageName": package.package_name,
                    "packageAmount": package.package_amount,
                    "packageDetails": package_details,
                },
            },
            status=status.HTTP_200_OK,
        )


class UpdateCodeStatusView(views.APIView):
    permission_classes = []

    def post(self, request, *args, **kwargs):
        is_updated = update_code_status(request)
        if is_updated:
            return Response(
                data={"message": "Code access updated"},
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                data={"message": "Unable to disable Code"},
                status=status.HTTP_409_CONFLICT,
            )


class SummaryMemberFranchiseeAdminView(views.APIView):
    permission_classes = [IsDeveloperUser | IsAdminUser | IsStaffUser]

    def post(self, request, *args, **kwargs):
        data = []
        accounts = Account.objects.count()
        data.append({"model": "Members", "summary": accounts})

        franchisees = Franchisee.objects.count()
        data.append({"model": "Franchisees", "summary": franchisees})
        return Response(
            data=data,
            status=status.HTTP_200_OK,
        )


class SummaryActivityStatsMemberView(views.APIView):
    permission_classes = [IsDeveloperUser | IsAdminUser | IsStaffUser | IsMemberUser]

    def post(self, request, *args, **kwargs):
        account_id = request.data.get("account_id")
        data = []
        account = get_object_or_404(Account, account_id=account_id)
        total_sales_match_points_today = find_total_sales_match_points_today(account)
        remaining_sales_match_points_today = account.package.flush_out_limit - total_sales_match_points_today

        data.append(
            {
                "flushout_limit": account.package.flush_out_limit,
                "remaining_sales_match_points_today": remaining_sales_match_points_today,
            }
        )

        return Response(
            data=data,
            status=status.HTTP_200_OK,
        )


class SummaryAdminView(views.APIView):
    permission_classes = [IsDeveloperUser | IsAdminUser | IsStaffUser]

    def post(self, request, *args, **kwargs):
        data = []
        entry_count = Activity.objects.filter(activity_type=ActivityType.ENTRY).count()
        data.append({"activity": ActivityType.ENTRY, "summary": entry_count})

        franchise_referrals = Activity.objects.filter(activity_type=ActivityType.FRANCHISE_COMMISSION).count()
        data.append({"activity": ActivityType.FRANCHISE_COMMISSION, "summary": franchise_referrals})

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

        franchise_referrals = Activity.objects.filter(
            account__account_id=account_id, activity_type=ActivityType.FRANCHISE_COMMISSION
        ).count()
        data.append({"activity": ActivityType.FRANCHISE_COMMISSION, "summary": franchise_referrals})

        leadership_bonus_count = Activity.objects.filter(
            account__account_id=account_id, activity_type=ActivityType.LEADERSHIP_BONUS
        ).count()
        data.append({"activity": ActivityType.LEADERSHIP_BONUS, "summary": leadership_bonus_count})

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
        ActivityFilter = [ActivityType.DOWNLINE_ENTRY, ActivityType.GLOBAL_POOL_BONUS, ActivityType.PV_SALES_MATCH]
        for activity in ActivityType:
            if activity not in ActivityFilter:
                activities = (
                    Activity.objects.filter(activity_type=activity)
                    .exclude(Q(wallet=WalletType.PV_LEFT_WALLET) | Q(wallet=WalletType.PV_RIGHT_WALLET))
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
            ActivityType.FRANCHISE_ENTRY,
            ActivityType.COMPANY_TAX,
            ActivityType.DOWNLINE_ENTRY,
            ActivityType.FLUSH_OUT_PENALTY,
        ]
        for activity in ActivityType:
            if activity not in ActivityFilter:
                activities = (
                    Activity.objects.filter(account__account_id=account_id, activity_type=activity)
                    .exclude(Q(wallet=WalletType.PV_LEFT_WALLET) | Q(wallet=WalletType.PV_RIGHT_WALLET))
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
        activities = (
            Activity.objects.filter(wallet=WalletType.C_WALLET)
            .values("activity_type")
            .annotate(
                running_total=Case(
                    When(
                        ~Q(activity_type=ActivityType.PAYOUT),
                        then=Sum(F("activity_amount")),
                    ),
                ),
                activity_total=Case(
                    When(
                        Q(activity_type=ActivityType.PAYOUT),
                        then=0 - (Sum(F("activity_amount"))),
                    ),
                    When(
                        ~Q(activity_type=ActivityType.PAYOUT),
                        then=(Sum(F("activity_amount"))),
                    ),
                ),
                payout_total=Case(
                    When(
                        Q(activity_type=ActivityType.PAYOUT),
                        then=0 - (Sum(F("activity_amount"))),
                    ),
                ),
            )
            .order_by("-activity_total")
        )
        wallet_running_total = activities.aggregate(
            total=Coalesce(Sum("running_total"), 0, output_field=DecimalField())
        ).get("total")

        wallet_total = activities.aggregate(total=Coalesce(Sum("activity_total"), 0, output_field=DecimalField())).get(
            "total"
        )
        wallet_total_payout = activities.aggregate(
            total=Coalesce(Sum("payout_total"), 0, output_field=DecimalField())
        ).get("total")

        data.append(
            {
                "wallet": WalletType.C_WALLET,
                "wallet_display": WalletType.C_WALLET + "_SUMMARY",
                "running_total": wallet_running_total,
                "total": wallet_total,
                "payout": wallet_total_payout,
                "details": activities,
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
                    .annotate(
                        running_total=Case(
                            When(
                                ~Q(activity_type=ActivityType.CASHOUT),
                                then=Sum(F("activity_amount")),
                            ),
                        ),
                        activity_total=Case(
                            When(
                                Q(activity_type=ActivityType.CASHOUT) & ~Q(status=ActivityStatus.DENIED),
                                then=0 - (Sum(F("activity_amount"))),
                            ),
                            When(
                                ~Q(activity_type=ActivityType.CASHOUT),
                                then=Sum(F("activity_amount")),
                            ),
                        ),
                        cashout_total=Case(
                            When(
                                Q(activity_type=ActivityType.CASHOUT),
                                then=0 - (Sum(F("activity_amount"))),
                            ),
                        ),
                    )
                    .order_by("-activity_total")
                )

                wallet_running_total = activities.aggregate(
                    total=Coalesce(Sum("running_total"), 0, output_field=DecimalField())
                ).get("total")
                wallet_total = activities.aggregate(
                    total=Coalesce(Sum("activity_total"), 0, output_field=DecimalField())
                ).get("total")
                wallet_total_cashout = activities.aggregate(
                    total=Coalesce(Sum("cashout_total"), 0, output_field=DecimalField())
                ).get("total")

                data.append(
                    {
                        "wallet": wallet,
                        "wallet_display": wallet + "_SUMMARY",
                        "running_total": wallet_running_total,
                        "total": wallet_total,
                        "cashout": wallet_total_cashout,
                        "details": activities,
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
        for wallet in [WalletType.PV_LEFT_WALLET, WalletType.PV_TOTAL_WALLET, WalletType.PV_RIGHT_WALLET]:
            activities = (
                Activity.objects.filter(account__account_id=account_id, wallet=wallet)
                .values("activity_type")
                .annotate(
                    running_total=Case(
                        When(
                            Q(activity_type=ActivityType.DOWNLINE_ENTRY),
                            then=Sum(F("activity_amount")),
                        ),
                    ),
                    flushout_total=Case(
                        When(
                            Q(activity_type=ActivityType.FLUSH_OUT_PENALTY),
                            then=Sum(F("activity_amount")),
                        ),
                    ),
                    activity_total=Sum(F("activity_amount")),
                )
                .order_by("-activity_total")
            )
            wallet_total = activities.aggregate(
                total=Coalesce(Sum("activity_total"), 0, output_field=DecimalField())
            ).get("total")
            wallet_running_total = activities.aggregate(
                total=Coalesce(Sum("running_total"), 0, output_field=DecimalField())
            ).get("total")

            wallet_flushout_total = activities.aggregate(
                total=Coalesce(Sum("flushout_total"), 0, output_field=DecimalField())
            ).get("total")

            data.append(
                {
                    "wallet": wallet,
                    "wallet_display": wallet + "_SUMMARY",
                    "total": wallet_total,
                    "running_total": wallet_running_total,
                    "flushout_total": wallet_flushout_total,
                }
            )

        return Response(
            data=data,
            status=status.HTTP_200_OK,
        )


class GetEnumTypesView(views.APIView):
    permission_classes = [IsDeveloperUser | IsAdminUser | IsStaffUser | IsMemberUser]

    def post(self, request, *args, **kwargs):
        data = get_all_enums()

        if data:
            return Response(
                data=data,
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                data={"message": "No Code Types available."},
                status=status.HTTP_404_NOT_FOUND,
            )


# Cashouts
class CashoutMethodView(views.APIView):
    permission_classes = [IsDeveloperUser | IsAdminUser | IsStaffUser | IsMemberUser]

    def post(self, request, *args, **kwargs):
        methods_arr = []

        for method in CashoutMethod:
            methods_arr.append(method)

        if methods_arr:
            return Response(
                data=methods_arr,
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                data={"message": "No Cashout Method currently Available."},
                status=status.HTTP_404_NOT_FOUND,
            )


class WalletCashoutView(views.APIView):
    permission_classes = [IsDeveloperUser | IsAdminUser | IsStaffUser | IsMemberUser]

    def post(self, request, *args, **kwargs):
        wallet = request.data.get("wallet")
        account_id = request.data.get("account_id")
        if get_wallet_can_cashout(wallet):
            no_cashout_today = not check_if_has_cashout_today(account_id, wallet)
            if no_cashout_today:
                has_no_pending_cashout = not check_if_has_pending_cashout(account_id, wallet)
                if has_no_pending_cashout:
                    return Response(
                        data={"message": "Cashout Available"},
                        status=status.HTTP_200_OK,
                    )
                else:
                    return Response(
                        data={"message": "Pending Cashout request existing for Wallet."},
                        status=status.HTTP_403_FORBIDDEN,
                    )
            else:
                return Response(
                    data={"message": "Max Cashout reached today."},
                    status=status.HTTP_403_FORBIDDEN,
                )
        else:
            return Response(
                data={"message": "Cashout currently unavailable."},
                status=status.HTTP_403_FORBIDDEN,
            )


class WalletScheduleView(views.APIView):
    permission_classes = [IsDeveloperUser | IsAdminUser | IsStaffUser | IsMemberUser]

    def post(self, request, *args, **kwargs):
        data = get_wallet_cashout_schedule()
        if data:
            return Response(
                data={"message": data},
                status=status.HTTP_200_OK,
            )
        return Response(
            data={"message": "Failed to get Cashout Schedule"},
            status=status.HTTP_403_FORBIDDEN,
        )


class WalletMaxAmountView(views.APIView):
    permission_classes = [IsDeveloperUser | IsAdminUser | IsStaffUser | IsMemberUser]

    def post(self, request, *args, **kwargs):
        wallet = request.data.get("wallet")
        account_id = request.data.get("account_id")
        amount = request.data.get("amount")
        if wallet is not None and account_id is not None and amount is not None:
            activities = (
                Activity.objects.filter(account__account_id=account_id, wallet=wallet)
                .values("activity_type")
                .annotate(
                    running_total=Case(
                        When(
                            ~Q(activity_type=ActivityType.CASHOUT),
                            then=Sum(F("activity_amount")),
                        ),
                    ),
                    activity_total=Case(
                        When(
                            Q(activity_type=ActivityType.CASHOUT),
                            then=0 - (Sum(F("activity_amount"))),
                        ),
                        When(
                            ~Q(activity_type=ActivityType.CASHOUT),
                            then=Sum(F("activity_amount")),
                        ),
                    ),
                    cashout_total=Case(
                        When(
                            Q(activity_type=ActivityType.CASHOUT),
                            then=0 - (Sum(F("activity_amount"))),
                        ),
                    ),
                )
                .order_by("-activity_total")
            )
            wallet_total = activities.aggregate(
                total=Coalesce(Sum("activity_total"), 0, output_field=DecimalField())
            ).get("total")
            if wallet_total - int(amount) >= 0:
                can_cashout, minimum_cashout_amount = compute_minimum_cashout_amount(amount, wallet)
                if can_cashout:
                    return Response(
                        data={"message": "Cashout Available"},
                        status=status.HTTP_200_OK,
                    )
                return Response(
                    data={"message": "Minimum amount of ₱" + str(minimum_cashout_amount)},
                    status=status.HTTP_403_FORBIDDEN,
                )
            else:
                return Response(
                    data={"message": "Cashout exceeds Balance"},
                    status=status.HTTP_403_FORBIDDEN,
                )
        else:
            return Response(
                data={"message": "No Current Balance for Cashout"},
                status=status.HTTP_403_FORBIDDEN,
            )


class WalletComputeTotalView(views.APIView):
    permission_classes = [IsDeveloperUser | IsAdminUser | IsStaffUser | IsMemberUser]

    def post(self, request, *args, **kwargs):
        data, message = compute_cashout_total(request)

        if data:
            return Response(
                data={"message": data},
                status=status.HTTP_200_OK,
            )
        return Response(
            data={"message": message},
            status=status.HTTP_400_BAD_REQUEST,
        )


class WalletTotalFeeView(views.APIView):
    permission_classes = [IsDeveloperUser | IsAdminUser | IsStaffUser | IsMemberUser]

    def post(self, request, *args, **kwargs):
        data = get_cashout_total_tax()
        if data:
            return Response(
                data=data,
                status=status.HTTP_200_OK,
            )
        return Response(
            data={"message": "Unable to retrieve Company Total Fee"},
            status=status.HTTP_400_BAD_REQUEST,
        )


class RequestCashoutView(views.APIView):
    permission_classes = [IsDeveloperUser | IsAdminUser | IsStaffUser | IsMemberUser]

    def post(self, request, *args, **kwargs):
        processed_request = process_create_cashout_request(request)
        print(processed_request)
        serializer = CreateActivitiesSerializer(data=processed_request)
        print(serializer)

        if serializer.is_valid():
            cashout = serializer.save()
            if cashout:
                return Response(data={"message": "Cashout Request created."}, status=status.HTTP_201_CREATED)
            else:
                return Response(
                    data={"message": "Unable to create Cashout Request."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            print(serializer.errors)
            return Response(
                data={"message": "Unable to create Cashout Request."},
                status=status.HTTP_400_BAD_REQUEST,
            )


class UpdateCashoutStatusView(views.APIView):
    permission_classes = [IsDeveloperUser | IsAdminUser | IsStaffUser]

    def post(self, request, *args, **kwargs):
        cashout, processed_request = process_save_cashout_status(request)
        serializer = CreateActivitiesSerializer(cashout, data=processed_request)
        if serializer.is_valid():
            updated_cashout = serializer.save()
            if updated_cashout.status != ActivityStatus.RELEASED:
                return Response(
                    data={"message": "Cashout updated."},
                    status=status.HTTP_201_CREATED,
                )

            payout = create_payout_activity(request, updated_cashout)
            if not payout:
                return Response(
                    data={"message": "Unable to create Payout Activity."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            company_earning = create_company_earning_activity(request, updated_cashout)
            if not company_earning:
                return Response(
                    data={"message": "Unable to create Company Tax Earning Activity."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            return Response(
                data={"message": "Cashout updated."},
                status=status.HTTP_201_CREATED,
            )
        else:
            return Response(
                data={"message": "Unable to update Cashout."},
                status=status.HTTP_400_BAD_REQUEST,
            )


# Franchise
class FranchiseeListViewSet(ModelViewSet):
    queryset = Franchisee.objects.all()
    serializer_class = FranchiseeListSerializer
    permission_classes = [IsDeveloperUser | IsAdminUser | IsStaffUser]
    http_method_names = ["get"]

    def get_queryset(self):
        id = self.request.query_params.get("id", None)
        queryset = Franchisee.objects.all()
        if id is not None:
            queryset = Franchisee.objects.filter(id=id)

        return queryset


class VerifyFranchiseeCodeView(views.APIView):
    permission_classes = []
    throttle_classes = [FivePerMinuteAnonThrottle]

    def post(self, request, *args, **kwargs):
        is_verified, message, activation_code, package = verify_code_details(request)
        if not is_verified:
            return Response(
                data={"message": message},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not package.is_franchise:
            return Response(
                data={"message": "Code not valid."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            data={
                "message": "Code valid.",
                "package": {
                    "codeType": activation_code.code_type,
                    "packagId": package.pk,
                    "packageName": package.package_name,
                    "packageAmount": package.package_amount,
                },
            },
            status=status.HTTP_200_OK,
        )


class CreateFranchiseeView(views.APIView):
    permission_classes = [IsDeveloperUser | IsAdminUser | IsStaffUser | IsMemberUser]

    def post(self, request, *args, **kwargs):
        is_verified, message, activation_code, package = verify_code_details(request)

        if not is_verified:
            return Response(
                data={"message": message},
                status=status.HTTP_400_BAD_REQUEST,
            )

        processed_request, code, package = process_create_franchisee_request(request)
        if not processed_request:
            print("here")
            return Response(
                data={"message": "Unable to create Franchisee."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = CreateFranchiseeSerializer(data=processed_request)
        if serializer.is_valid():
            new_franchisee = serializer.save()
            is_valid = comp_plan(request, new_franchisee, package, code)
            if is_valid:
                code.update_status(Franchisee)
                return Response(data={"message": "Franchisee created."}, status=status.HTTP_201_CREATED)

            return Response(
                data={"message": "Unable to create Franchisee."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        else:
            print(serializer.errors)
            return Response(
                data={"message": "Unable to create Franchisee."},
                status=status.HTTP_400_BAD_REQUEST,
            )
