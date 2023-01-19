from rest_framework import status, views, permissions
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from django.core.signing import Signer, BadSignature
from django.db.models import Q, Prefetch, F, Value as V, query, Count, Sum, Case, When, DecimalField
from django.db.models.functions import Concat, Coalesce
from django.shortcuts import get_object_or_404
from vanguard.permissions import IsDeveloperUser, IsAdminUser, IsStaffUser, IsMemberUser
from vanguard.throttle import FivePerMinuteAnonThrottle, FifteenPerMinuteAnonThrottle
from accounts.serializers import (
    CashoutMethodSerializer,
    AccountSerializer,
    AccountProfileSerializer,
    AccountListSerializer,
    AccountReferralsSerializer,
    AccountWalletSerializer,
    GenealogyAccountAdminSerializer,
    GenealogyAccountMemberSerializer,
    BinaryAccountProfileSerializer,
    UserAccountAvatarSerializer,
    UserAccountSerializer,
)
from accounts.models import Account, CashoutMethod
from accounts.enums import ParentSide
from accounts.services import (
    is_valid_uuid,
    process_create_account_request,
    activate_account,
    process_media,
    transform_account_form_data_to_json,
    transform_admin_account_form_data_to_json,
    update_user_status,
    verify_account_creation,
    redact_string,
    verify_account_name,
    verify_parent_account,
    verify_parent_side,
    verify_sponsor_account,
)
from core.models import Code
from core.enums import ActivityStatus, CodeStatus, WalletType, ActivityType, CodeType
from core.services import comp_plan, create_leadership_bonus_activity, verify_code_details
from users.models import User


class UserAccountViewSet(ModelViewSet):
    queryset = Account.objects.all()
    serializer_class = UserAccountSerializer
    permission_classes = [IsDeveloperUser | IsAdminUser | IsStaffUser]
    http_method_names = ["get"]

    def get_queryset(self):
        account_id = self.request.query_params.get("account_id", None)
        queryset = Account.objects.exclude(is_deleted=True).filter(account_id=account_id).all()
        if queryset.exists():
            return queryset


class UserAccountAvatarViewSet(ModelViewSet):
    queryset = Account.objects.all()
    serializer_class = UserAccountAvatarSerializer
    permission_classes = [IsDeveloperUser | IsAdminUser | IsStaffUser | IsMemberUser]

    def get_queryset(self):
        user = User.objects.get(id=self.request.user.pk, is_active=True)

        if user is not None:
            queryset = Account.objects.filter(user=user)

            return queryset


class AccountProfileViewSet(ModelViewSet):
    queryset = Account.objects.all()
    serializer_class = AccountProfileSerializer
    permission_classes = [IsDeveloperUser | IsAdminUser | IsStaffUser | IsMemberUser]
    http_method_names = ["get"]

    def get_queryset(self):
        account_id = self.request.query_params.get("account_id", None)
        queryset = Account.objects.exclude(is_deleted=True).filter(account_id=account_id).all()
        if queryset.exists():
            return queryset


class AccountCashoutMethodsViewSet(ModelViewSet):
    queryset = CashoutMethod.objects.all()
    serializer_class = CashoutMethodSerializer
    permission_classes = [IsDeveloperUser | IsAdminUser | IsStaffUser | IsMemberUser]
    http_method_names = ["get"]

    def get_queryset(self):
        account_id = self.request.query_params.get("account_id", None)
        queryset = CashoutMethod.objects.filter(account__account_id=account_id).all()
        if queryset.exists():
            return queryset


class AccountListViewSet(ModelViewSet):
    queryset = Account.objects.all()
    serializer_class = AccountListSerializer
    permission_classes = [IsDeveloperUser | IsAdminUser | IsStaffUser]
    http_method_names = ["get"]

    def get_queryset(self):
        queryset = Account.objects.exclude(is_deleted=True).all()
        if queryset.exists():
            return queryset


class AccountReferralsViewSet(ModelViewSet):
    queryset = Account.objects.all()
    serializer_class = AccountReferralsSerializer
    permission_classes = [IsDeveloperUser | IsAdminUser | IsStaffUser]
    http_method_names = ["get"]

    def get_queryset(self):
        queryset = Account.objects.exclude(is_deleted=True).all()
        if queryset.exists():
            return queryset


class TopAccountWalletViewSet(ModelViewSet):
    queryset = Account.objects.all()
    serializer_class = AccountWalletSerializer
    permission_classes = [IsDeveloperUser | IsAdminUser | IsStaffUser]
    http_method_names = ["get"]

    def get_queryset(self):
        queryset = (
            Account.objects.exclude(is_deleted=True)
            .annotate(
                wallet_amount=Coalesce(
                    Sum(
                        Case(
                            When(
                                Q(activity__activity_type=ActivityType.CASHOUT)
                                & ~Q(activity__status=ActivityStatus.DENIED),
                                then=0 - F("activity__activity_amount"),
                            ),
                            When(
                                ~Q(activity__activity_type=ActivityType.CASHOUT)
                                & ~Q(activity__wallet=WalletType.C_WALLET),
                                then=F("activity__activity_amount"),
                            ),
                        )
                    ),
                    0,
                    output_field=DecimalField(),
                )
            )
            .all()
            .order_by("-wallet_amount")[:5]
        )
        if queryset.exists():
            return queryset


class GenealogyAccountAdminViewSet(ModelViewSet):
    queryset = Account.objects.all()
    serializer_class = GenealogyAccountAdminSerializer
    permission_classes = [IsDeveloperUser | IsAdminUser | IsStaffUser]
    http_method_names = ["get"]

    def get_queryset(self):
        account_id = self.request.query_params.get("account_id", None)
        account = []

        if account_id is not None and is_valid_uuid(account_id):
            account = Account.objects.get(account_id=account_id)
        if account_id is not None and is_valid_uuid(account_id) == False:
            account = get_object_or_404(Account, id=account_id.lstrip("0"))

        if account is not None:
            queryset = Account.objects.prefetch_related(
                Prefetch(
                    "children",
                    queryset=Account.objects.prefetch_related(
                        Prefetch(
                            "children",
                            queryset=Account.objects.prefetch_related(
                                Prefetch(
                                    "children",
                                    queryset=Account.objects.prefetch_related(
                                        Prefetch(
                                            "children",
                                            queryset=Account.objects.prefetch_related(
                                                Prefetch(
                                                    "children",
                                                    queryset=Account.objects.order_by("parent_side").all(),
                                                )
                                            )
                                            .order_by("parent_side")
                                            .all(),
                                        )
                                    )
                                    .order_by("parent_side")
                                    .all(),
                                )
                            )
                            .order_by("parent_side")
                            .all(),
                        )
                    )
                    .order_by("parent_side")
                    .all(),
                ),
            ).filter(id=account.pk)

            for member in queryset:
                member.all_left_children_count = len(member.get_all_children_side(parent_side=ParentSide.LEFT))
                member.all_right_children_count = len(member.get_all_children_side(parent_side=ParentSide.RIGHT))

            return queryset


class GenealogyAccountMemberViewSet(ModelViewSet):
    queryset = Account.objects.all()
    serializer_class = GenealogyAccountMemberSerializer
    permission_classes = [IsDeveloperUser | IsAdminUser | IsStaffUser | IsMemberUser]
    http_method_names = ["get"]

    def get_queryset(self):
        account_id = self.request.query_params.get("account_id", None)
        account = []

        if account_id is not None and is_valid_uuid(account_id):
            account = get_object_or_404(Account, account_id=account_id)
            account = Account.objects.get(account_id=account_id)
        if account_id is not None and is_valid_uuid(account_id) == False:
            account = get_object_or_404(Account, id=account_id.lstrip("0"))

        if account is not None:
            user_account = Account.objects.get(user=self.request.user)
            children = user_account.get_all_children()

            if account in children or account == user_account:
                queryset = Account.objects.prefetch_related(
                    Prefetch(
                        "children",
                        queryset=Account.objects.prefetch_related(
                            Prefetch(
                                "children",
                                queryset=Account.objects.prefetch_related(
                                    Prefetch(
                                        "children",
                                        queryset=Account.objects.prefetch_related(
                                            Prefetch(
                                                "children",
                                                queryset=Account.objects.prefetch_related(
                                                    Prefetch(
                                                        "children",
                                                        queryset=Account.objects.order_by("parent_side").all(),
                                                    )
                                                )
                                                .order_by("parent_side")
                                                .all(),
                                            )
                                        )
                                        .order_by("parent_side")
                                        .all(),
                                    )
                                )
                                .order_by("parent_side")
                                .all(),
                            )
                        )
                        .order_by("parent_side")
                        .all(),
                    ),
                ).filter(id=account.pk)

                for member in queryset:
                    member.all_left_children_count = len(member.get_all_children_side(parent_side=ParentSide.LEFT))
                    member.all_right_children_count = len(member.get_all_children_side(parent_side=ParentSide.RIGHT))

                return queryset


class BinaryAccountProfileViewSet(ModelViewSet):
    queryset = Account.objects.all()
    serializer_class = BinaryAccountProfileSerializer
    permission_classes = [IsDeveloperUser | IsAdminUser | IsStaffUser | IsMemberUser]
    http_method_names = ["get"]

    def get_queryset(self):
        queryset = Account.objects.prefetch_related(
            Prefetch(
                "children",
            ),
        ).all()

        account_id = self.request.query_params.get("account_id", None)

        if account_id is not None:
            queryset = queryset.filter(account_id=account_id)

            for member in queryset:
                member.all_left_children_count = len(member.get_all_children_side(parent_side=ParentSide.LEFT))
                member.all_right_children_count = len(member.get_all_children_side(parent_side=ParentSide.RIGHT))

            return queryset


# Custom Views POST
class CreateAccountView(views.APIView):
    permission_classes = []
    throttle_classes = [FifteenPerMinuteAnonThrottle]

    def post(self, request, *args, **kwargs):
        is_verified = verify_account_creation(request) and verify_sponsor_account(request)
        if is_verified:
            processed_request, code, package = process_create_account_request(request)
            if not processed_request:
                return Response(
                    data={"message": "Unable to create Account."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            serializer = AccountSerializer(data=processed_request)
            if serializer.is_valid():
                new_member = serializer.save()
                is_valid = comp_plan(request, new_member, package, code)
                if is_valid:
                    activate_account(new_member)
                    code.update_status(Account)
                    return Response(data={"message": "Account created."}, status=status.HTTP_201_CREATED)

                return Response(
                    data={"message": "Unable to create Account."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            else:
                return Response(
                    data={"message": "Unable to create Account."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            return Response(
                data={"message": "Unable to create Account. Extreme Side Validation"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class UpdateAccountAdminView(views.APIView):
    permission_classes = [IsDeveloperUser | IsAdminUser | IsStaffUser]

    def post(self, request, *args, **kwargs):
        data = transform_admin_account_form_data_to_json(request.data)
        account = Account.objects.get(account_id=data["account_id"])

        serializer = AccountSerializer(account, data=data, partial=True)
        if serializer.is_valid():
            updated_member = serializer.save()
            if updated_member:
                return Response(
                    data={"message": "Profile updated"},
                    status=status.HTTP_200_OK,
                )
            return Response(
                data={"message": "Unable to update Account"},
                status=status.HTTP_409_CONFLICT,
            )
        else:
            print(serializer.errors)
            return Response(
                data={"message": "Unable to update Account"},
                status=status.HTTP_409_CONFLICT,
            )


class UpdateAccountView(views.APIView):
    permission_classes = [IsDeveloperUser | IsAdminUser | IsStaffUser | IsMemberUser]

    def post(self, request, *args, **kwargs):
        account = Account.objects.get(user=request.user)
        data = transform_account_form_data_to_json(request.data)

        serializer = AccountSerializer(account, data=data, partial=True)
        if serializer.is_valid():
            updated_member = serializer.save()
            if updated_member:
                return Response(
                    data={"message": "Profile updated"},
                    status=status.HTTP_200_OK,
                )
            return Response(
                data={"message": "Unable to update Account"},
                status=status.HTTP_409_CONFLICT,
            )
        else:
            return Response(
                data={"message": "Unable to update Account"},
                status=status.HTTP_409_CONFLICT,
            )


class VerifyAccountView(views.APIView):
    permission_classes = [IsDeveloperUser | IsAdminUser | IsStaffUser]

    def post(self, request, *args, **kwargs):
        account_id = request.data.get("account_id").lstrip("0")
        if account_id:
            try:
                Account.objects.get(id=account_id)
                return Response(
                    data={"message": "Account existing."},
                    status=status.HTTP_200_OK,
                )
            except Account.DoesNotExist:
                return Response(
                    data={"message": "Account does not exist."},
                    status=status.HTTP_404_NOT_FOUND,
                )
        else:
            return Response(
                data={"message": "Account does not exist."},
                status=status.HTTP_404_NOT_FOUND,
            )


class VerifySponsorAccountNumberView(views.APIView):
    permission_classes = []
    throttle_classes = [FifteenPerMinuteAnonThrottle]

    def post(self, request, *args, **kwargs):
        sponsor_account_id = request.data.get("sponsor_account_id").lstrip("0")
        if sponsor_account_id:
            try:
                account = Account.objects.get(id=sponsor_account_id)
                fullname = redact_string(account.get_full_name())
                return Response(
                    data={"message": "Sponsor Account Number verified", "account": fullname},
                    status=status.HTTP_200_OK,
                )
            except Account.DoesNotExist:
                return Response(
                    data={"message": "Invalid Sponsor Account Number"},
                    status=status.HTTP_404_NOT_FOUND,
                )
        else:
            return Response(
                data={"message": "Invalid Sponsor Account Number"},
                status=status.HTTP_404_NOT_FOUND,
            )


class VerifyParentAccountNumberView(views.APIView):
    permission_classes = []
    throttle_classes = [FifteenPerMinuteAnonThrottle]

    def post(self, request, *args, **kwargs):
        parent_account_id = request.data.get("parent_account_id").lstrip("0")
        if parent_account_id:
            is_verified, parent = verify_parent_account(request)
            if is_verified:
                fullname = redact_string(parent.get_full_name())
                return Response(
                    data={"message": "Parent Account Number verified", "account": fullname},
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    data={"message": "Invalid Parent Account Number"},
                    status=status.HTTP_404_NOT_FOUND,
                )
        else:
            return Response(
                data={"message": "Invalid Parent Account Number"},
                status=status.HTTP_404_NOT_FOUND,
            )


class VerifyParentSideView(views.APIView):
    permission_classes = []
    throttle_classes = [FifteenPerMinuteAnonThrottle]

    def post(self, request, *args, **kwargs):
        is_verified = verify_parent_side(request)
        if is_verified:
            return Response(
                data={"message": "Extreme side validation success"},
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                data={"message": "Extreme side validation failed"},
                status=status.HTTP_409_CONFLICT,
            )


class VerifyExtremeSide(views.APIView):
    permission_classes = [IsDeveloperUser | IsAdminUser | IsStaffUser | IsMemberUser]

    def post(self, request, *args, **kwargs):
        can_sponsor = verify_sponsor_account(request)
        if can_sponsor:
            return Response(
                data={"message": "OK"},
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                data={"message": "Extreme side validation failed"},
                status=status.HTTP_409_CONFLICT,
            )


class VerifyAccountName(views.APIView):
    permission_classes = []
    throttle_classes = [FifteenPerMinuteAnonThrottle]

    def post(self, request, *args, **kwargs):
        is_verified = verify_account_name(request)
        if is_verified:
            return Response(
                data={"message": "Account Name validation success"},
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                data={"message": "Account Name validation failed"},
                status=status.HTTP_409_CONFLICT,
            )


class UpgradeAccountView(views.APIView):
    permission_classes = [IsDeveloperUser | IsAdminUser | IsStaffUser | IsMemberUser]

    def post(self, request, *args, **kwargs):
        is_verified, message, activation_code, package = verify_code_details(request)

        if not is_verified:
            return Response(
                data={"message": message},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if activation_code.code_type != CodeType.UPGRADE or package.is_franchise:
            return Response(
                data={"message": "Code not valid. Must be an Upgrade Code."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        account = Account.objects.get(account_id=request.data["account_id"])
        if package is None and account is None:
            return Response(
                data={"message": "Unable to upgrade Account."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if package.package_amount <= account.package.package_amount:
            return Response(
                data={"message": "Downgrade Account not available."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = {"activation_code": activation_code.pk, "package": package.pk}
        serializer = AccountSerializer(account, data=data, partial=True)
        if serializer.is_valid():
            upgraded_member = serializer.save()
            is_valid = comp_plan(request, upgraded_member, package, activation_code)
            if is_valid:
                activation_code.update_status(Account)
                return Response(data={"message": "Account upgraded."}, status=status.HTTP_200_OK)

            return Response(
                data={"message": "Unable to upgrade Account."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            data={"message": "Unable to upgrade Account."},
            status=status.HTTP_400_BAD_REQUEST,
        )


class VerifyCreateAccountLinkView(views.APIView):
    permission_classes = []

    def get(self, request, *args, **kwargs):
        signer = Signer()
        data = self.request.query_params.get("data", None)
        try:
            unsigned_obj = signer.unsign_object(data)
            return Response(
                data=unsigned_obj,
                status=status.HTTP_200_OK,
            )
        except BadSignature:
            return Response(
                data={"message": "Invalid URL"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    def post(self, request, *args, **kwargs):
        signer = Signer()
        signed_obj = signer.sign_object(request.data)
        url = request.build_absolute_uri("/odcwebapi/accounts/verify?data=" + signed_obj)
        return Response(
            data={"url": url},
            status=status.HTTP_200_OK,
        )


class UpdateUserStatusView(views.APIView):
    permission_classes = []

    def post(self, request, *args, **kwargs):
        is_updated = update_user_status(request)
        if is_updated:
            return Response(
                data={"message": "Account access updated"},
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                data={"message": "Unable to disable Account"},
                status=status.HTTP_409_CONFLICT,
            )


class TestCreateView(views.APIView):
    permission_classes = []

    def post(self, request, *args, **kwargs):
        can_sponsor = verify_sponsor_account(request)
        if can_sponsor:
            return Response(
                data={"message": "OK"},
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                data={"message": "Extreme side validation failed"},
                status=status.HTTP_409_CONFLICT,
            )
