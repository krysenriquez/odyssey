import json
import random
import uuid
from django.http import QueryDict
from django.shortcuts import get_object_or_404
from accounts.models import Account, AvatarInfo, CashoutMethod
from accounts.enums import AccountStatus
from core.enums import CodeStatus
from core.services import get_code_details
from users.services import create_new_user


def is_valid_uuid(val):
    try:
        uuid.UUID(str(val))
        return True
    except ValueError:
        return False


def redact_string(string):
    temp = [k for k in string]

    for j in random.sample(range(len(string) - 1), len(string) // 2):
        temp[j] = "*"
    return "".join(temp)


def process_create_account_request(request):
    activation_code, package = get_code_details(request.data["activation_code"])

    if activation_code.status != CodeStatus.ACTIVE:
        return False

    if package.is_franchise:
        return False

    if activation_code and package:
        data = {
            "parent": request.data["parent_account_id"].lstrip("0"),
            "parent_side": request.data["parent_side"],
            "activation_code": activation_code.pk,
            "referrer": request.data["sponsor_account_id"].lstrip("0"),
            "first_name": request.data["first_name"],
            "middle_name": request.data["middle_name"],
            "last_name": request.data["last_name"],
            "created_by": request.user.pk,
            "package": package.pk,
            "personal_info": request.data["personal_info"],
            "contact_info": request.data["contact_info"],
            "address_info": request.data["address_info"],
            "avatar_info": request.data["avatar_info"],
        }

        if isinstance(request.data["user"], str) and request.data["user"] == "link":
            data["user"] = request.user.pk
        elif isinstance(request.data["user"], dict):
            new_user = create_new_user(request.data["user"])
            if new_user:
                data["user"] = new_user.pk

        return data, activation_code, package


def verify_account_creation(request):
    parent = get_object_or_404(Account, id=request.data["parent_account_id"].lstrip("0"))
    sibling = parent.children.exclude(parent_side=request.data["parent_side"]).first()

    if parent.parent is None:
        return True

    if sibling is None and parent.parent_side != request.data["parent_side"]:
        return False

    return True


def verify_parent_account(request):
    parent = get_object_or_404(Account, id=request.data["parent_account_id"].lstrip("0"))
    children_count = parent.children.all().count()

    if children_count >= 2:
        return False, parent

    return True, parent


def verify_parent_side(request):
    parent = get_object_or_404(Account, id=request.data["parent_account_id"].lstrip("0"))
    children_count = parent.children.all().count()

    if parent.parent is None:
        return True

    if children_count >= 2:
        return False

    sibling = parent.children.exclude(parent_side=request.data["parent_side"]).first()
    if sibling is None and parent.parent_side != request.data["parent_side"]:
        return False

    return True


def verify_account_name(request):
    first_name = request.data["first_name"].strip()
    middle_name = request.data["middle_name"].strip()
    last_name = request.data["last_name"].strip()
    queryset = Account.objects.filter(
        first_name__exact=first_name, middle_name__exact=middle_name, last_name__exact=last_name
    )

    if queryset.exists():
        return False
    return True


def activate_account(account=None):
    Account.objects.update_or_create(id=account.pk, defaults={"account_status": AccountStatus.ACTIVE})


def verify_sponsor_account(request):
    parent = get_object_or_404(Account, id=request.data["parent_account_id"].lstrip("0"))
    sponsor = get_object_or_404(Account, id=request.data["sponsor_account_id"].lstrip("0"))

    grandparents = parent.get_all_parents_with_extreme_side(parent_side=request.data["parent_side"])
    grandparents.append({"account": parent})

    can_sponsor = next((grandparent for grandparent in grandparents if grandparent["account"] == sponsor), [])

    return bool(can_sponsor)


def create_new_cashout_method(request, account):
    data = {
        "account": account,
        "account_name": request.data["cashout_method"]["account_name"],
        "account_number": request.data["cashout_method"]["account_number"],
        "method": request.data["cashout_method"]["method"],
    }

    if request.data["cashout_method"]["method"] == "Other/s":
        data["method"] = request.data["cashout_method"]["others"]

    cashout_method = CashoutMethod.objects.create(**data)

    return cashout_method


def update_user_status(request):
    account = get_object_or_404(Account, account_id=request.data["account_id"])
    is_updated = account.user.update_is_active()
    return is_updated


def transform_admin_account_form_data_to_json(request):
    data = {}
    for key, value in request.items():
        if type(value) != str:
            data[key] = value
            continue
        if "{" in value or "[" in value:
            try:
                data[key] = json.loads(value)
            except ValueError:
                data[key] = value
        else:
            data[key] = value

    data["account_id"] = uuid.UUID(request["account_id"].strip('"'))

    if request.get("avatar_info['id']") is not None:
        data["avatar_info"] = {
            "id": request["avatar_info['id']"],
            "file_attachment": request["avatar_info['fileAttachment']"],
            "file_name": request["avatar_info['fileName']"],
        }

    return data


def transform_account_form_data_to_json(request):
    data = {}
    for key, value in request.items():
        if type(value) != str:
            data[key] = value
            continue
        if "{" in value or "[" in value:
            try:
                data[key] = json.loads(value)
            except ValueError:
                data[key] = value
        else:
            data[key] = value

    if request.get("avatar_info['id']") is not None:
        data["avatar_info"] = {
            "id": request["avatar_info['id']"],
            "file_attachment": request["avatar_info['fileAttachment']"],
            "file_name": request["avatar_info['fileName']"],
        }

    return data


def process_media(account, attachment):
    avatar_info, created = AvatarInfo.objects.get_or_create(account=account)

    if created:
        avatar_info.file_attachment(attachment)
        avatar_info.save()

    return avatar_info
