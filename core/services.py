import decimal
import logging
import calendar
import string, random
from django.db.models.functions import TruncDate, Coalesce
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q, Sum, Case, When, F, DecimalField
from django.utils import timezone
from django.shortcuts import get_object_or_404
from tzlocal import get_localzone

# from accounts.models import Account
from accounts.enums import ParentSide, Gender
from core.models import Activity, Setting, Code, Package, ReferralBonus, LeadershipBonus
from core.enums import ActivityType, ActivityStatus, WalletType, Settings, CodeStatus, CodeType

logger = logging.getLogger("ocmLogger")


# Core Settings
def get_object_or_none(classmodel, **kwargs):
    try:
        return classmodel.objects.get(**kwargs)
    except classmodel.DoesNotExist:
        return None


def get_all_enums():
    side_arr = []
    for side in ParentSide:
        side_arr.append(side)

    gender_arr = []
    for gender in Gender:
        gender_arr.append(gender)

    type_arr = []
    for type in CodeType:
        type_arr.append(type)

    status_arr = []
    for status in CodeStatus:
        status_arr.append(status)

    setting_arr = []
    for setting in Settings:
        setting_arr.append(setting)

    data = {
        "CodeStatuses": status_arr,
        "CodeTypes": type_arr,
        "ParentSides": side_arr,
        "Genders": gender_arr,
        "Settings": setting_arr,
    }

    return data


def get_settings():
    return Setting.objects.all()


def get_setting(property):
    return Setting.objects.get(property=property).value


def generate_code():
    size = int(get_setting(Settings.CODE_LENGTH))
    chars = string.ascii_uppercase + string.digits
    return "".join(random.choice(chars) for _ in range(size))


def create_codes(self, validated_data):
    quantity = validated_data.pop("quantity")

    if quantity:
        for i in range(int(quantity)):
            generated_code = generate_code()
            if generated_code:
                code = Code.objects.create(**validated_data, code=generated_code)
                code.save()


def update_code_status(request):
    code = get_object_or_404(Code, code=request.data["code"])
    is_updated = code.activate_deactivate()
    return is_updated


def get_wallet_cashout_schedule():
    days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    calendar.setfirstweekday(calendar.SUNDAY)
    data = []
    for wallet in [
        WalletType.B_WALLET,
        WalletType.F_WALLET,
        WalletType.GC_WALLET,
    ]:
        property = "%s%s" % (wallet, "_CASHOUT_DAY")
        if property:
            day = int(get_setting(property=property))
            data.append({wallet: " is open during %s" % days[day]})
    else:
        return data


def get_wallet_can_cashout(wallet):
    if wallet == WalletType.F_WALLET or wallet == WalletType.B_WALLET or wallet == WalletType.GC_WALLET:
        property = "%s%s" % (wallet, "_CASHOUT_DAY")
        if property:
            day = int(get_setting(property=property))
            if day == timezone.localtime().isoweekday():
                return True
            else:
                has_override = "%s%s" % (wallet, "_CASHOUT_OVERRIDE")
                if bool(int(get_setting(property=has_override))):
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


def check_if_has_pending_cashout(account_id, wallet):
    return Activity.objects.filter(
        Q(activity_type=ActivityType.CASHOUT)
        & Q(Q(status=ActivityStatus.REQUESTED) | Q(status=ActivityStatus.APPROVED)),
        account__account_id=account_id,
        wallet=wallet,
    )


def compute_cashout_total(request):
    data = {}
    admin_fee = get_cashout_total_tax()
    total_cashout = decimal.Decimal(request.data["amount"]) * ((100 - get_cashout_total_tax()) / 100)

    if total_cashout and admin_fee:
        data["activity_admin_fee"] = admin_fee
        data["activity_total_amount"] = total_cashout
        return data, "Valid"

    return data, "Unable to retrieve Total Cashout Amount"


def compute_minimum_cashout_amount(amount):
    minimum_cashout_amount = get_setting(Settings.MINIMUM_CASHOUT_AMOUNT)

    return amount >= minimum_cashout_amount, minimum_cashout_amount


def process_create_franchisee_request(request):
    activation_code, package = get_code_details(request.data["activation_code"])

    if activation_code.status != CodeStatus.ACTIVE:
        return False

    if not package.is_franchise:
        return False

    if activation_code and package:
        data = {
            "activation_code": activation_code.pk,
            "package": package.pk,
            "referrer": request.data["sponsor_account_id"].lstrip("0"),
            "first_name": request.data["first_name"],
            "middle_name": request.data["middle_name"],
            "last_name": request.data["last_name"],
            "gender": request.data["gender"],
            "email_address": request.data["email_address"],
            "contact_number": request.data["contact_number"],
            "street": request.data["street"],
            "city": request.data["city"],
            "state": request.data["state"],
            "created_by": request.user.pk,
        }

        return data, activation_code, package


# Core Activities
def get_cashout_total_tax():
    company_earnings = get_setting(Settings.COMPANY_CASHOUT_FEE_PERCENTAGE)
    return company_earnings


def get_code_details(activation_code=None):
    activation_code = get_object_or_404(Code, code=activation_code)
    package = get_object_or_404(Package, id=activation_code.package.pk)

    if package:
        return activation_code, package


def verify_code_details(request):
    activation_code, package = get_code_details(request.data["activation_code"])

    match activation_code.status:
        case CodeStatus.ACTIVE:
            if package is None:
                return False, "No Package associated to Code", activation_code, None
            return True, "Code valid", activation_code, package
        case CodeStatus.DEACTIVATED:
            return False, "Code has been deactivated", activation_code, package
        case CodeStatus.EXPIRED:
            return False, "Code has expired", activation_code, package
        case CodeStatus.USED:
            return False, "Code is no longer active.", activation_code, package


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
    status=None,
    wallet=None,
    content_type=None,
    object_id=None,
    user=None,
):
    if user.is_authenticated:
        return Activity.objects.create(
            account=account,
            activity_type=activity_type,
            activity_amount=activity_amount,
            status=status,
            wallet=wallet,
            content_type=content_type,
            object_id=object_id,
            created_by=user,
        )
    else:
        return Activity.objects.create(
            account=account,
            activity_type=activity_type,
            activity_amount=activity_amount,
            status=status,
            wallet=wallet,
            content_type=content_type,
            object_id=object_id,
        )


def process_create_cashout_request(request):
    from accounts.models import Account, CashoutMethod
    from accounts.services import create_new_cashout_method

    content_type = ContentType.objects.get(model="cashoutmethod")
    account = get_object_or_404(Account, account_id=request.data["account_id"])

    if account:
        data = {
            "account": account.pk,
            "activity_type": ActivityType.CASHOUT,
            "activity_amount": request.data["activity_amount"],
            "wallet": request.data["wallet"],
            "status": ActivityStatus.REQUESTED,
            "note": request.data["note"],
            "details": [
                {
                    "action": "Cashout Requested",
                    "created_by": request.user.pk,
                }
            ],
            "created_by": request.user.pk,
            "content_type": content_type.pk,
            "object_id": "",
        }

        if (
            isinstance(request.data["cashout_method"]["cashout_method_id"], str)
            and request.data["cashout_method"]["cashout_method_id"]
        ):
            cashout_method = get_object_or_404(CashoutMethod, id=request.data["cashout_method"]["cashout_method_id"])
            data["object_id"] = cashout_method.pk
        elif isinstance(request.data["cashout_method"], dict):
            cashout_method = create_new_cashout_method(request, account)
            data["object_id"] = cashout_method.pk

        return data


def process_save_cashout_status(request):
    cashout = Activity.objects.get(id=request.data["activity_number"].lstrip("0"))
    data = {}
    details = []
    if cashout:
        if request.data["status"] == ActivityStatus.APPROVED:
            details.append({"action": "Cashout Approved", "created_by": request.user.pk})
        elif request.data["status"] == ActivityStatus.RELEASED:
            details.append({"action": "Cashout Released", "created_by": request.user.pk})
        elif request.data["status"] == ActivityStatus.DENIED:
            details.append({"action": "Cashout Denied", "created_by": request.user.pk})

        data["details"] = details
        data["status"] = request.data["status"]

        return cashout, data


def create_payout_activity(request, updated_cashout):
    if updated_cashout:
        content_type = ContentType.objects.get(model="activity")
        total_tax = (100 - get_cashout_total_tax()) / 100

        return create_activity(
            account=updated_cashout.account,
            activity_type=ActivityType.PAYOUT,
            activity_amount=updated_cashout.activity_amount * total_tax,
            status=ActivityStatus.DONE,
            wallet=WalletType.C_WALLET,
            content_type=content_type,
            object_id=updated_cashout.pk,
            user=request.user,
        )


def create_company_earning_activity(request, updated_cashout):
    if updated_cashout:
        content_type = ContentType.objects.get(model="activity")
        total_tax_earning = get_cashout_total_tax() / 100

        return create_activity(
            account=updated_cashout.account,
            activity_type=ActivityType.COMPANY_TAX,
            activity_amount=updated_cashout.activity_amount * total_tax_earning,
            status=ActivityStatus.DONE,
            wallet=WalletType.C_WALLET,
            content_type=content_type,
            object_id=updated_cashout.pk,
            user=request.user,
        )


# Entry
def create_entry_activity(request, account=None, new_member_package=None, code=None):
    if new_member_package.is_franchise:
        content_type = ContentType.objects.get(model="franchisee")

        return create_activity(
            account=account.referrer,
            activity_type=ActivityType.FRANCHISE_ENTRY,
            activity_amount=new_member_package.package_amount,
            status=ActivityStatus.DONE,
            wallet=WalletType.C_WALLET,
            content_type=content_type,
            object_id=account.pk,
            user=request.user,
        )

    content_type = ContentType.objects.get(model="account")
    if code.code_type == CodeType.FREE_SLOT:
        return create_activity(
            account=account,
            activity_type=ActivityType.ENTRY,
            activity_amount=0,
            status=ActivityStatus.DONE,
            wallet=WalletType.C_WALLET,
            content_type=content_type,
            object_id=account.pk,
            user=request.user,
        )

    return create_activity(
        account=account,
        activity_type=ActivityType.ENTRY,
        activity_amount=new_member_package.package_amount,
        status=ActivityStatus.DONE,
        wallet=WalletType.C_WALLET,
        content_type=content_type,
        object_id=account.pk,
        user=request.user,
    )


def create_referral_activity(request, sponsor=None, account=None, new_member_package=None, code=None):
    if new_member_package.is_franchise:
        content_type = ContentType.objects.get(model="franchisee")
        franchise_commission_percentage = get_setting(Settings.FRANCHISE_COMMISSION_PERCENTAGE) / 100
        return create_activity(
            account=sponsor,
            activity_type=ActivityType.FRANCHISE_COMMISSION,
            activity_amount=new_member_package.package_amount * franchise_commission_percentage,
            status=ActivityStatus.DONE,
            wallet=WalletType.F_WALLET,
            content_type=content_type,
            object_id=account.pk,
            user=request.user,
        )

    content_type = ContentType.objects.get(model="account")
    direct_referral_percentage = get_setting(Settings.DIRECT_REFERRAL_PERCENTAGE) / 100
    if code.code_type == CodeType.FREE_SLOT:
        return create_activity(
            account=sponsor,
            activity_type=ActivityType.DIRECT_REFERRAL,
            activity_amount=0,
            status=ActivityStatus.DONE,
            wallet=WalletType.B_WALLET,
            content_type=content_type,
            object_id=account.pk,
            user=request.user,
        )

    referral = create_activity(
        account=sponsor,
        activity_type=ActivityType.DIRECT_REFERRAL,
        activity_amount=new_member_package.package_amount * direct_referral_percentage,
        status=ActivityStatus.DONE,
        wallet=WalletType.B_WALLET,
        content_type=content_type,
        object_id=account.pk,
        user=request.user,
    )

    if referral:
        create_referral_bonus_activity(request, sponsor, new_member_package)

        return referral


def create_referral_bonus_activity(request, sponsor=None, new_member_package=None):
    referral_count_by_package = sponsor.get_all_direct_referral_by_package_count(new_member_package)
    referral_bonus_count = get_setting(Settings.REFERRAL_BONUS_COUNT)
    sponsor_referral_bonus = get_referral_bonus_details(sponsor.package, new_member_package)
    point_value_conversion = get_setting(Settings.POINT_VALUE_CONVERSION)

    if referral_count_by_package % referral_bonus_count == 0 and sponsor_referral_bonus:
        return create_activity(
            account=sponsor,
            activity_type=ActivityType.REFERRAL_BONUS,
            activity_amount=sponsor_referral_bonus.point_value * point_value_conversion,
            status=ActivityStatus.DONE,
            wallet=WalletType.B_WALLET,
            user=request.user,
        )


def create_downline_entry_activity(request, parent=None, child=None, child_side=None, new_member_package=None):
    content_type = ContentType.objects.get(model="account")

    match child_side:
        case ParentSide.LEFT:
            return create_activity(
                account=parent,
                activity_type=ActivityType.DOWNLINE_ENTRY,
                activity_amount=new_member_package.point_value,
                status=ActivityStatus.DONE,
                wallet=WalletType.PV_LEFT_WALLET,
                content_type=content_type,
                object_id=child.pk,
                user=request.user,
            )
        case ParentSide.RIGHT:
            return create_activity(
                account=parent,
                activity_type=ActivityType.DOWNLINE_ENTRY,
                activity_amount=new_member_package.point_value,
                status=ActivityStatus.DONE,
                wallet=WalletType.PV_RIGHT_WALLET,
                content_type=content_type,
                object_id=child.pk,
                user=request.user,
            )


def create_sales_match_activity(request, parent=None, sales_match_amount_pv=None):
    content_type = ContentType.objects.get(model="activity")
    pv_conversion = get_setting(Settings.POINT_VALUE_CONVERSION)

    pv_sales_match = create_activity(
        account=parent,
        activity_type=ActivityType.PV_SALES_MATCH,
        activity_amount=sales_match_amount_pv,
        status=ActivityStatus.DONE,
        wallet=WalletType.PV_TOTAL_WALLET,
        user=request.user,
    )

    if pv_sales_match:
        create_activity(
            account=parent,
            activity_type=ActivityType.PV_SALES_MATCH,
            activity_amount=-abs(sales_match_amount_pv),
            status=ActivityStatus.DONE,
            wallet=WalletType.PV_LEFT_WALLET,
            content_type=content_type,
            object_id=pv_sales_match.pk,
            user=request.user,
        )
        create_activity(
            account=parent,
            activity_type=ActivityType.PV_SALES_MATCH,
            activity_amount=-abs(sales_match_amount_pv),
            status=ActivityStatus.DONE,
            wallet=WalletType.PV_RIGHT_WALLET,
            content_type=content_type,
            object_id=pv_sales_match.pk,
            user=request.user,
        )

        fifth_pair_amount = create_fifth_pairing(request, parent, pv_sales_match.pk)

        if ((sales_match_amount_pv * pv_conversion) - fifth_pair_amount) > 0:
            sales_match = create_activity(
                account=parent,
                activity_type=ActivityType.SALES_MATCH,
                activity_amount=(sales_match_amount_pv * pv_conversion) - fifth_pair_amount,
                status=ActivityStatus.DONE,
                wallet=WalletType.B_WALLET,
                content_type=content_type,
                object_id=pv_sales_match.pk,
                user=request.user,
            )

            if sales_match:
                create_leadership_bonus_activity(request, sales_match_amount_pv, parent, pv_sales_match.pk)


def create_leadership_bonus_activity(request, sales_match_amount_pv=None, account=None, pv_sales_match_pk=None):
    pv_conversion = get_setting(Settings.POINT_VALUE_CONVERSION)
    two_level_referrers = account.get_two_level_referrer()
    content_type = ContentType.objects.get(model="activity")

    for referrer in two_level_referrers:
        leadership_bonus = get_leadership_bonus_details(referrer["package"], referrer["level"])
        if leadership_bonus is not None:
            leadership_bonus_pv_percentage = leadership_bonus.point_value_percentage / 100

            create_activity(
                account=referrer["account"],
                activity_type=ActivityType.LEADERSHIP_BONUS,
                activity_amount=(sales_match_amount_pv * leadership_bonus_pv_percentage) * pv_conversion,
                status=ActivityStatus.DONE,
                wallet=WalletType.B_WALLET,
                content_type=content_type,
                object_id=pv_sales_match_pk,
                user=request.user,
            )


def create_fifth_pairing(request, account=None, pv_sales_match_pk=None):
    fifth_pair_percentage = get_setting(Settings.FIFTH_PAIR_PERCENTAGE) / 100
    pv_conversion = get_setting(Settings.POINT_VALUE_CONVERSION)
    content_type = ContentType.objects.get(model="activity")

    total_fifth_pair_amount = (
        Activity.objects.filter(account=account, wallet=WalletType.GC_WALLET)
        .values("activity_type")
        .annotate(
            activity_total=Case(
                When(
                    Q(activity_type=ActivityType.FIFTH_PAIR),
                    then=Sum(F("activity_amount")),
                ),
            )
        )
        .aggregate(total=Coalesce(Sum("activity_total"), 0, output_field=DecimalField()))
        .get("total")
    )

    pv_total_wallet = (
        Activity.objects.filter(account=account, wallet=WalletType.PV_TOTAL_WALLET)
        .values("activity_type")
        .annotate(
            activity_total=Sum(F("activity_amount")),
        )
        .aggregate(total=Coalesce(Sum("activity_total"), 0, output_field=DecimalField()))
        .get("total")
    )

    total_fifth_pair_pv_amount = total_fifth_pair_amount / pv_conversion

    remaining_fifth_pair_pv_amount = pv_total_wallet - (total_fifth_pair_pv_amount / fifth_pair_percentage)

    fifth_pair_pv_match = (
        remaining_fifth_pair_pv_amount - (remaining_fifth_pair_pv_amount % 100)
    ) * fifth_pair_percentage

    if fifth_pair_pv_match:
        fifth_pair = create_activity(
            account=account,
            activity_type=ActivityType.FIFTH_PAIR,
            activity_amount=fifth_pair_pv_match * pv_conversion,
            status=ActivityStatus.DONE,
            wallet=WalletType.GC_WALLET,
            content_type=content_type,
            object_id=pv_sales_match_pk,
            user=request.user,
        )

        return fifth_pair.activity_amount

    return 0


def create_flushout_activity(
    request,
    parent=None,
    strong_side_wallet_total=None,
    weak_side_wallet_total=None,
    strong_side_wallet=None,
):
    content_type = ContentType.objects.get(model="activity")
    penalty_weak = get_setting(Settings.FLUSH_OUT_PENALTY_PERCENTAGE_WEAK) / 100
    penalty_strong = get_setting(Settings.FLUSH_OUT_PENALTY_PERCENTAGE_STRONG) / 100

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


def get_pv_wallets_info(parent=None, child_side=None):
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
        return left_wallet_total, right_wallet_total, WalletType.PV_LEFT_WALLET
    elif right_wallet_total > left_wallet_total:
        return right_wallet_total, left_wallet_total, WalletType.PV_RIGHT_WALLET
    else:
        match child_side:
            case ParentSide.LEFT:
                return right_wallet_total, left_wallet_total, WalletType.PV_RIGHT_WALLET
            case ParentSide.RIGHT:
                return left_wallet_total, right_wallet_total, WalletType.PV_LEFT_WALLET


def comp_plan(request, new_member, new_member_package, code):
    entry_activity = create_entry_activity(request, new_member, new_member_package, code)
    if new_member.referrer and entry_activity:
        referral_activity = create_referral_activity(request, new_member.referrer, new_member, new_member_package, code)

        if referral_activity is None:
            return False

    if new_member_package.is_franchise:
        return True

    if code.code_type == CodeType.FREE_SLOT and referral_activity:
        return True

    parents = new_member.get_all_parents_with_side()
    for parent in parents:
        current_parent = parent["account"]
        current_level = parent["level"]
        current_parent_package = get_package_details(parent["package"])

        downline_entry_activity = create_downline_entry_activity(
            request, current_parent, new_member, parent["side"], new_member_package
        )

        if downline_entry_activity is None:
            continue

        strong_side_wallet_total, weak_side_wallet_total, strong_side_wallet = get_pv_wallets_info(
            current_parent, parent["side"]
        )
        if strong_side_wallet_total > 0 and weak_side_wallet_total > 0:
            if strong_side_wallet_total > weak_side_wallet_total:
                sales_match_amount_pv = weak_side_wallet_total
            else:
                sales_match_amount_pv = new_member_package.point_value

            total_sales_match_points_today = find_total_sales_match_points_today(current_parent)
            remaining_sales_match_points_today = current_parent_package.flush_out_limit - total_sales_match_points_today

            if remaining_sales_match_points_today - sales_match_amount_pv >= 0:
                create_sales_match_activity(request, current_parent, sales_match_amount_pv)
            else:
                if remaining_sales_match_points_today > 0:
                    create_sales_match_activity(request, current_parent, remaining_sales_match_points_today)
                    create_flushout_activity(
                        request,
                        current_parent,
                        strong_side_wallet_total - remaining_sales_match_points_today,
                        weak_side_wallet_total - remaining_sales_match_points_today,
                        strong_side_wallet,
                    )
                else:
                    create_flushout_activity(
                        request,
                        current_parent,
                        strong_side_wallet_total,
                        weak_side_wallet_total,
                        strong_side_wallet,
                    )
    else:
        return True
