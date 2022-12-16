import logging
import string, random
from django.db.models.functions import TruncDate, Coalesce
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q, Sum, Case, When, F, DecimalField
from django.utils import timezone
from django.shortcuts import get_object_or_404
from tzlocal import get_localzone

# from accounts.models import Account
from accounts.enums import ParentSide
from core.models import Activity, Setting, Code, Package, ReferralBonus, LeadershipBonus
from core.enums import ActivityType, ActivityStatus, WalletType, Settings, CodeStatus

logger = logging.getLogger("ocmLogger")

# Core Settings
def get_object_or_none(classmodel, **kwargs):
    try:
        return classmodel.objects.get(**kwargs)
    except classmodel.DoesNotExist:
        return None


def get_settings():
    return Setting.objects.all()


def get_setting(property):
    return Setting.objects.get(property=property).value


def generate_code():
    size = int(get_setting(Settings.CODE_LENGTH))
    chars = string.ascii_uppercase + string.digits
    return "".join(random.choice(chars) for _ in range(size))


def get_wallet_can_cashout(wallet):
    if wallet == WalletType.F_WALLET and wallet == WalletType.B_WALLET:
        property = "%s%s" % (wallet, "_CASHOUT_DAY")
        if property:
            day = int(get_setting(property=property))
            if day == timezone.localtime().isoweekday():
                return True
            else:
                return False


def check_if_has_cashout_today(account_id, wallet):
    local_tz = get_localzone()
    return Activity.objects.annotate(modified_local_tz=TruncDate("modified", tzinfo=local_tz)).filter(
        account__account_id=account_id,
        activity_type=ActivityType.CASHOUT,
        wallet=wallet,
        modified_local_tz=timezone.localtime().date(),
    )


def check_if_has_cashout_today(account_id, wallet):
    local_tz = get_localzone()
    return Activity.objects.annotate(modified_local_tz=TruncDate("modified", tzinfo=local_tz)).filter(
        account__account_id=account_id,
        activity_type=ActivityType.CASHOUT,
        wallet=wallet,
        modified_local_tz=timezone.localtime().date(),
    )


def check_if_has_pending_cashout(account_id, wallet):
    return Activity.objects.filter(
        Q(status=ActivityStatus.REQUESTED) | Q(status=ActivityStatus.APPROVED),
        account__account_id=account_id,
        wallet=wallet,
    )


# Core Activities
def get_code_details(activation_code=None):
    activation_code = get_object_or_404(Code, code=activation_code, status=CodeStatus.ACTIVE)
    package = get_object_or_404(Package, id=activation_code.package.pk)

    if package:

        return activation_code, package


def get_package_details(package=None):
    return get_object_or_404(Package, id=package.pk)


def get_referral_bonus_details(package_referrer=None, package_referred=None):
    return get_object_or_none(ReferralBonus, package_referrer=package_referrer, package_referred=package_referred)


def get_leadership_bonus_details(package=None, level=None):
    return get_object_or_none(LeadershipBonus, package=package, level=level)


def create_activity(
    account=None,
    activity_type=None,
    activity_amount=None,
    wallet=None,
    content_type=None,
    object_id=None,
    user=None,
):
    return Activity.objects.create(
        account=account,
        activity_type=activity_type,
        activity_amount=activity_amount,
        wallet=wallet,
        content_type=content_type,
        object_id=object_id,
        created_by=user,
    )


def create_entry_activity(request, account=None, new_member_package=None):
    content_type = ContentType.objects.get(model="account")

    create_activity(
        account=account,
        activity_type=ActivityType.ENTRY,
        activity_amount=new_member_package.package_amount,
        wallet=WalletType.C_WALLET,
        content_type=content_type,
        object_id=account.pk,
        user=request.user,
    )


def create_referral_activity(request, sponsor=None, account=None, new_member_package=None):
    content_type = ContentType.objects.get(model="account")

    referral = create_activity(
        account=sponsor,
        activity_type=ActivityType.DIRECT_REFERRAL,
        activity_amount=new_member_package.package_amount
        * (get_setting(Settings.DIRECT_REFERRAL_PERCENTAGE) / 100),
        wallet=WalletType.B_WALLET,
        content_type=content_type,
        object_id=account.pk,
        user=request.user,
    )

    if referral:
        create_referral_bonus_activity(request, sponsor, new_member_package)


def create_referral_bonus_activity(request, sponsor=None, new_member_package=None):
    referral_count_by_package = sponsor.get_all_direct_referral_by_package_count(new_member_package)
    referral_bonus_count = get_setting(Settings.REFERRAL_BONUS_COUNT)
    sponsor_referral_bonus = get_referral_bonus_details(sponsor.package, new_member_package)

    if referral_count_by_package % referral_bonus_count == 0 and sponsor_referral_bonus:
        create_activity(
            account=sponsor,
            activity_type=ActivityType.REFERRAL_BONUS,
            activity_amount=sponsor_referral_bonus.point_value,
            wallet=WalletType.B_WALLET,
            user=request.user,
        )


def create_downline_entry_activity(request, parent=None, child=None, child_side=None, new_member_package=None):
    content_type = ContentType.objects.get(model="account")

    match child_side:
        case ParentSide.LEFT:
            create_activity(
                account=parent,
                activity_type=ActivityType.DOWNLINE_ENTRY,
                activity_amount=new_member_package.point_value,
                wallet=WalletType.PV_LEFT_WALLET,
                content_type=content_type,
                object_id=child.pk,
                user=request.user,
            )
        case ParentSide.RIGHT:
            create_activity(
                account=parent,
                activity_type=ActivityType.DOWNLINE_ENTRY,
                activity_amount=new_member_package.point_value,
                wallet=WalletType.PV_RIGHT_WALLET,
                content_type=content_type,
                object_id=child.pk,
                user=request.user,
            )


def create_sales_match_activity(request, parent=None, sales_match_amount=None):
    content_type = ContentType.objects.get(model="activity")

    pv_sales_match = create_activity(
        account=parent,
        activity_type=ActivityType.PV_SALES_MATCH,
        activity_amount=sales_match_amount,
        wallet=WalletType.PV_TOTAL_WALLET,
        user=request.user,
    )

    if pv_sales_match:
        create_activity(
            account=parent,
            activity_type=ActivityType.PV_SALES_MATCH,
            activity_amount=-abs(sales_match_amount),
            wallet=WalletType.PV_LEFT_WALLET,
            content_type=content_type,
            object_id=pv_sales_match.pk,
            user=request.user,
        )

        create_activity(
            account=parent,
            activity_type=ActivityType.PV_SALES_MATCH,
            activity_amount=-abs(sales_match_amount),
            wallet=WalletType.PV_RIGHT_WALLET,
            content_type=content_type,
            object_id=pv_sales_match.pk,
            user=request.user,
        )

        create_activity(
            account=parent,
            activity_type=ActivityType.SALES_MATCH,
            activity_amount=sales_match_amount * get_setting(Settings.POINT_VALUE_CONVERSION),
            wallet=WalletType.B_WALLET,
            content_type=content_type,
            object_id=pv_sales_match.pk,
            user=request.user,
        )


def create_flushout_activity(
    request,
    parent=None,
    strong_side_wallet_total=None,
    weak_side_wallet_total=None,
    is_wallet_equal=None,
    strong_side_wallet=None,
):
    content_type = ContentType.objects.get(model="activity")
    penalty_weak = get_setting(Settings.FLUSH_OUT_PENALTY_PERCENTAGE_WEAK) / 100
    penalty_strong = get_setting(Settings.FLUSH_OUT_PENALTY_PERCENTAGE_STRONG) / 100
    # strong_side_wallet_total= 50
    # 50 * .5
    # weak_side_wallet_total = 40
    # (40 * -1)
    if is_wallet_equal:
        create_activity(
            account=parent,
            activity_type=ActivityType.FLUSH_OUT_PENALTY,
            activity_amount=-abs(strong_side_wallet_total * penalty_strong),
            wallet=WalletType.PV_LEFT_WALLET,
            user=request.user,
        )
        create_activity(
            account=parent,
            activity_type=ActivityType.FLUSH_OUT_PENALTY,
            activity_amount=-abs(strong_side_wallet_total * penalty_strong),
            wallet=WalletType.PV_RIGHT_WALLET,
            user=request.user,
        )
    else:
        match strong_side_wallet:
            case WalletType.PV_LEFT_WALLET:
                create_activity(
                    account=parent,
                    activity_type=ActivityType.FLUSH_OUT_PENALTY,
                    activity_amount=-abs(strong_side_wallet_total * penalty_strong),
                    wallet=WalletType.PV_LEFT_WALLET,
                    user=request.user,
                )
                create_activity(
                    account=parent,
                    activity_type=ActivityType.FLUSH_OUT_PENALTY,
                    activity_amount=-abs(weak_side_wallet_total * penalty_weak),
                    wallet=WalletType.PV_RIGHT_WALLET,
                    user=request.user,
                )
            case WalletType.PV_RIGHT_WALLET:
                create_activity(
                    account=parent,
                    activity_type=ActivityType.FLUSH_OUT_PENALTY,
                    activity_amount=-abs(weak_side_wallet_total * penalty_weak),
                    wallet=WalletType.PV_LEFT_WALLET,
                    user=request.user,
                )
                create_activity(
                    account=parent,
                    activity_type=ActivityType.FLUSH_OUT_PENALTY,
                    activity_amount=-abs(strong_side_wallet_total * penalty_strong),
                    wallet=WalletType.PV_RIGHT_WALLET,
                    user=request.user,
                )


def find_total_sales_match_points_today(parent=None):
    sales_match_points_today = (
        Activity.objects.annotate(created_local_tz=TruncDate("created", tzinfo=get_localzone()))
        .filter(
            account=parent,
            wallet=WalletType.PV_TOTAL_WALLET,
            created_local_tz=timezone.localtime().date(),
            activity_type=ActivityType.PV_SALES_MATCH,
        )
        .aggregate(total=Coalesce(Sum("activity_amount"), 0, output_field=DecimalField()))
        .get("total")
    )

    return sales_match_points_today


def get_pv_wallets_info(parent=None):
    left_wallet_total = (
        Activity.objects.filter(account=parent, wallet=WalletType.PV_LEFT_WALLET)
        .values("activity_type")
        .annotate(
            activity_total=Case(
                When(
                    Q(activity_type=ActivityType.FLUSH_OUT_PENALTY),
                    then=(Sum(F("activity_amount"))),
                ),
                When(
                    Q(activity_type=ActivityType.PV_SALES_MATCH),
                    then=(Sum(F("activity_amount"))),
                ),
                When(
                    Q(activity_type=ActivityType.DOWNLINE_ENTRY),
                    then=Sum(F("activity_amount")),
                ),
            ),
        )
        .aggregate(total=Coalesce(Sum("activity_total"), 0, output_field=DecimalField()))
        .get("total")
    )
    right_wallet_total = (
        Activity.objects.filter(account=parent, wallet=WalletType.PV_RIGHT_WALLET)
        .values("activity_type")
        .annotate(
            activity_total=Case(
                When(
                    Q(activity_type=ActivityType.FLUSH_OUT_PENALTY),
                    then=(Sum(F("activity_amount"))),
                ),
                When(
                    Q(activity_type=ActivityType.PV_SALES_MATCH),
                    then=(Sum(F("activity_amount"))),
                ),
                When(
                    Q(activity_type=ActivityType.DOWNLINE_ENTRY),
                    then=Sum(F("activity_amount")),
                ),
            ),
        )
        .aggregate(total=Coalesce(Sum("activity_total"), 0, output_field=DecimalField()))
        .get("total")
    )

    if left_wallet_total > right_wallet_total:
        return left_wallet_total, right_wallet_total, False, WalletType.PV_LEFT_WALLET
    elif right_wallet_total > left_wallet_total:
        return right_wallet_total, left_wallet_total, False, WalletType.PV_RIGHT_WALLET
    else:
        return left_wallet_total, right_wallet_total, True, WalletType.PV_LEFT_WALLET


def comp_plan(request, new_member, new_member_package):
    create_entry_activity(request, new_member, new_member_package)
    if new_member.referrer:
        create_referral_activity(request, new_member.referrer, new_member, new_member_package)

    parents = new_member.get_all_parents_with_side()
    for parent in parents:
        current_parent = parent["account"]
        current_level = parent["level"]
        current_parent_package = get_package_details(parent["package"])
        create_downline_entry_activity(request, current_parent, new_member, parent["side"], new_member_package)
        strong_side_wallet_total, weak_side_wallet_total, equal_values, strong_side_wallet = get_pv_wallets_info(
            current_parent
        )
        print(strong_side_wallet_total, weak_side_wallet_total)
        if strong_side_wallet_total > 0 and weak_side_wallet_total > 0:
            sales_match_amount = new_member_package.point_value
            total_sales_match_points_today = find_total_sales_match_points_today(current_parent)
            remaining_sales_match_points_today = (
                current_parent_package.flush_out_limit - total_sales_match_points_today
            )
            if remaining_sales_match_points_today - sales_match_amount >= 0:
                create_sales_match_activity(request, current_parent, sales_match_amount)
            else:
                if remaining_sales_match_points_today > 0:
                    create_sales_match_activity(request, current_parent, remaining_sales_match_points_today)
                    create_flushout_activity(
                        request,
                        current_parent,
                        strong_side_wallet_total - remaining_sales_match_points_today,
                        weak_side_wallet_total - remaining_sales_match_points_today,
                        equal_values,
                        strong_side_wallet,
                    )
                else:
                    create_flushout_activity(
                        request,
                        current_parent,
                        strong_side_wallet_total,
                        weak_side_wallet_total,
                        equal_values,
                        strong_side_wallet,
                    )

        # On get all parents with sides
        # Add sponsors of parent up to 2 levels
        # Loop through each sponso on this complan to check their packages, if their is a 2nd package
        # Get leadership bonus

        # if current_level <= package["leadership_bonus"]["level"]:
        #     current_unilevel_amount_property = "UNILEVEL_AMOUNT_{0}_GEN".format(current_level)
        #     create_unilevel_activity(request, curre
