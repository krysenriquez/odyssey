from rest_framework import status, views, permissions
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from django.db.models import Q, Prefetch, F, Value as V, query, Count, Sum, Case, When
from django.db.models.functions import Concat, Coalesce
from vanguard.permissions import IsDeveloperUser, IsAdminUser, IsStaffUser, IsMemberUser
from accounts.serializers import (
    AccountSerializer,
    AccountProfileSerializer,
    AccountListSerializer,
    AccountReferralsSerializer,
    AccountWalletSerializer,
    GenealogyAccountSerializer,
    BinaryAccountProfileSerializer,
)
from accounts.models import Account
from accounts.enums import ParentSide
from accounts.services import process_create_account_request, activate_account, verify_account_creation
from core.models import Code
from core.enums import CodeStatus, WalletType, ActivityType
from core.services import comp_plan


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
                                & ~Q(activity__wallet=WalletType.C_WALLET),
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
                )
            )
            .all()
            .order_by("-wallet_amount")[:5]
        )
        if queryset.exists():
            return queryset


class GenealogyAccountAdminViewSet(ModelViewSet):
    queryset = Account.objects.all()
    serializer_class = GenealogyAccountSerializer
    permission_classes = [IsDeveloperUser | IsAdminUser | IsStaffUser]
    http_method_names = ["get"]

    def get_queryset(self):
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
        ).all()

        account_id = self.request.query_params.get("account_id", None)
        account_number = self.request.query_params.get("account_number", None)

        if account_id is None and account_number is not None:
            queryset = queryset.filter(id=account_number.lstrip("0"))

            for member in queryset:
                member.all_left_children_count = len(member.get_all_children_side(parent_side=ParentSide.LEFT))
                member.all_right_children_count = len(member.get_all_children_side(parent_side=ParentSide.RIGHT))

            return queryset

        elif account_id is not None and account_number is not None:
            account = Account.objects.get(account_id=account_id)
            children = account.get_all_children()
            child = Account.objects.get(id=account_number.lstrip("0"))

            if child in children or child == account:
                queryset = queryset.filter(id=account_number.lstrip("0"))

                for member in queryset:
                    member.all_left_children_count = len(member.get_all_children_side(parent_side=ParentSide.LEFT))
                    member.all_right_children_count = len(
                        member.get_all_children_side(parent_side=ParentSide.RIGHT)
                    )

                return queryset

        elif account_id is not None and account_number is None:
            queryset = queryset.filter(account_id=account_id)

            for member in queryset:
                member.all_left_children_count = len(member.get_all_children_side(parent_side=ParentSide.LEFT))
                member.all_right_children_count = len(member.get_all_children_side(parent_side=ParentSide.RIGHT))

            return queryset


class GenealogyAccountMemberViewSet(ModelViewSet):
    queryset = Account.objects.all()
    serializer_class = GenealogyAccountSerializer
    permission_classes = [IsDeveloperUser | IsAdminUser | IsStaffUser | IsMemberUser]
    http_method_names = ["get"]

    def get_queryset(self):
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
        ).all()

        account_id = self.request.query_params.get("account_id", None)
        account_number = self.request.query_params.get("account_number", None)

        if account_id is None and account_number is not None and self.request.user.user_type:
            queryset = queryset.filter(id=account_number.lstrip("0"))

            for member in queryset:
                member.all_left_children_count = len(member.get_all_children_side(parent_side=ParentSide.LEFT))
                member.all_right_children_count = len(member.get_all_children_side(parent_side=ParentSide.RIGHT))

            return queryset

        elif account_id is not None and account_number is not None:
            account = Account.objects.get(account_id=account_id)
            children = account.get_all_children()
            child = Account.objects.get(id=account_number.lstrip("0"))

            if child in children or child == account:
                queryset = queryset.filter(id=account_number.lstrip("0"))

                for member in queryset:
                    member.all_left_children_count = len(member.get_all_children_side(parent_side=ParentSide.LEFT))
                    member.all_right_children_count = len(
                        member.get_all_children_side(parent_side=ParentSide.RIGHT)
                    )

                return queryset

        elif account_id is not None and account_number is None:
            queryset = queryset.filter(account_id=account_id)

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
    permission_classes = [IsDeveloperUser | IsAdminUser | IsStaffUser | IsMemberUser]

    def post(self, request, *args, **kwargs):
        is_verified = verify_account_creation(request)
        if is_verified:
            processed_request, package, code = process_create_account_request(request)
            serializer = AccountSerializer(data=processed_request)

            if serializer.is_valid():
                new_member = serializer.save()
                # code.update_status()
                comp_plan(request, new_member, package)
                activate_account(new_member)
                return Response(data={"message": "Account created."}, status=status.HTTP_201_CREATED)
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


class VerifySponsorCodeView(views.APIView):
    permission_classes = [IsDeveloperUser | IsAdminUser | IsStaffUser | IsMemberUser]

    def post(self, request, *args, **kwargs):
        code_type = request.data.get("code_type")
        code = request.data.get("code")
        parent = request.data.get("parent")

        try:
            activation_code = Code.objects.get(code_type=code_type, code=code)
            activation_code.update_status()
        except Code.DoesNotExist:
            return Response(
                data={"message": code_type.title() + " Code does not exist."},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            upline = Account.objects.get(id=parent)
        except Account.DoesNotExist:
            return Response(
                data={"message": "Upline Account does Not Exist."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if activation_code.account:
            try:
                sponsor = Account.objects.get(pk=activation_code.account.pk)
                children = sponsor.get_all_children()
            except Account.DoesNotExist:
                return Response(
                    data={"message": "Sponsor Account does Not Exist."},
                    status=status.HTTP_404_NOT_FOUND,
                )
        else:
            return Response(
                data={"message": code_type.title() + " Code " + code + " not linked to any Account."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if upline in children or sponsor == upline:
            if activation_code.status == CodeStatus.DEACTIVATED:
                return Response(
                    data={
                        "message": code_type.title() + " Code currently deactivated.",
                    },
                    status=status.HTTP_410_GONE,
                )
            elif activation_code.status == CodeStatus.USED:
                return Response(
                    data={
                        "message": code_type.title() + " Code already been used.",
                    },
                    status=status.HTTP_409_CONFLICT,
                )
            elif activation_code.status == CodeStatus.EXPIRED:
                return Response(
                    data={
                        "message": code_type.title() + " Code has already expired.",
                    },
                    status=status.HTTP_409_CONFLICT,
                )
            else:
                return Response(
                    data={
                        "message": code_type.title() + " Code valid.",
                        "sponsor": str(sponsor.id).zfill(5),
                        "sponsor_name": sponsor.first_name + " " + sponsor.last_name,
                    },
                    status=status.HTTP_200_OK,
                )
        else:
            return Response(
                data={
                    "message": code_type.title() + " Code could only be used on Direct Downlines.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )
