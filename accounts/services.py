from django.shortcuts import get_object_or_404
from accounts.models import Account
from accounts.enums import AccountStatus
from core.services import get_code_details
from users.services import create_new_user


def process_create_account_request(request):
    activation_code, package = get_code_details(request.data["activation_code"])

    if activation_code and package:
        data = {
            "parent": request.data["parent_account_id"].lstrip("0"),
            "parent_side": request.data["parent_side"],
            "activation_code": activation_code.pk,
            "referrer": request.data["sponsor_account_id"].lstrip("0"),
            "first_name": request.data["first_name"],
            "last_name": request.data["last_name"],
            "created_by": request.user.pk,
            "package": package.pk,
            "personal_info": [{}],
            "contact_info": [{}],
            "address_info": [{}],
            "avatar_info": [{}],
        }

        if isinstance(request.data["user"], str) and request.data["user"] == "link":
            data["user"] = request.user.pk
        elif isinstance(request.data["user"], dict):
            new_user = create_new_user(request.data["user"])
            if new_user:
                data["user"] = new_user.pk

        return data, package, activation_code


def verify_account_creation(request):
    parent = get_object_or_404(Account, id=request.data["parent_account_id"].lstrip("0"))
    sibling = parent.children.exclude(parent_side=request.data["parent_side"]).first()

    if sibling is None:
        if parent.parent_side != request.data["parent_side"]:
            return False
    return True


def activate_account(account=None):
    Account.objects.update_or_create(id=account.pk, defaults={"account_status": AccountStatus.ACTIVE})
