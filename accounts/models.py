import uuid
from django.db import models
from django.utils import timezone
from django.db.models.functions import TruncDate
from tzlocal import get_localzone
from dateutil.relativedelta import relativedelta
from accounts.enums import AccountStatus, Gender, ParentSide


def account_avatar_directory(instance, filename):
    return "accounts/{0}/avatar/{1}".format(instance.account.account_id, filename)


class Account(models.Model):
    account_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    parent = models.ForeignKey(
        "self",
        related_name="children",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    parent_side = models.CharField(max_length=10, choices=ParentSide.choices, null=True, blank=True)
    activation_code = models.ForeignKey(
        "core.Code",
        related_name="account_activated",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    package = models.ForeignKey(
        "core.Package",
        related_name="account_package",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    referrer = models.ForeignKey(
        "self",
        related_name="referrals",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    first_name = models.CharField(max_length=255, null=True, blank=True)
    middle_name = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )
    last_name = models.CharField(max_length=255, null=True, blank=True)
    account_status = models.CharField(
        max_length=11,
        choices=AccountStatus.choices,
        default=AccountStatus.DRAFT,
    )
    user = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        related_name="account_user",
        null=True,
        blank=True,
    )
    created_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        related_name="account_created",
        null=True,
    )
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    deleted = models.DateTimeField(blank=True, null=True)
    is_deleted = models.BooleanField(
        default=False,
    )

    class Meta:
        ordering = ["-created", "-id"]

    def get_full_name(self):
        return "%s %s %s" % (self.first_name, self.middle_name, self.last_name)

    def get_account_name(self):
        return "%s %s" % (self.first_name, self.last_name)

    def get_account_number(self):
        return str(self.id).zfill(5)

    def get_account_package(self):
        return "%s" % (self.package.package_name)

    def get_account_package_amount(self):
        return "%s" % (self.package.package_amount)

    def get_all_children_side(self, children=None, parent_side=None):
        if children is None:
            children = []
        for account in self.children.all():
            if account.parent_side == parent_side:
                children.append(account)
                account.get_all_children(children)
        return children

    def get_all_children(self, children=None):
        if children is None:
            children = []
        for account in self.children.all():
            children.append(account)
            account.get_all_children(children)
        return children

    def get_all_parents(self, parents=None):
        if parents is None:
            parents = []
        if self.parent:
            parents.append(self.parent)
            self.parent.get_all_parents(parents)
        return parents

    def get_all_parents_with_side(self, parents=None, level=None):
        if parents is None:
            parents = []
            level = 0
        if self.parent:
            level = level + 1
            parents.append(
                {"account": self.parent, "side": self.parent_side, "level": level, "package": self.parent.package}
            )
            self.parent.get_all_parents_with_side(parents, level)
        return parents

    def get_all_direct_referral_count(self):
        return self.referrals.all().count()

    def get_all_direct_referral_by_package_count(self, package=None):
        return self.referrals.all().filter(package=package).count()

    def get_all_direct_referral_month(self):
        local_tz = get_localzone()
        nth_of_the_month = self.created.astimezone(local_tz).day

        current_month_date = timezone.localtime().date() + relativedelta(day=int(nth_of_the_month))
        previous_month_date = current_month_date - relativedelta(months=1, day=int(nth_of_the_month))
        next_month_date = current_month_date + relativedelta(months=1, day=int(nth_of_the_month))

        if int(nth_of_the_month) < int(timezone.localtime().day):
            return (
                self.referrals.annotate(created_local_tz=TruncDate("created", tzinfo=local_tz))
                .filter(
                    created_local_tz__gte=current_month_date,
                    created_local_tz__lte=next_month_date,
                )
                .all()
            )
        else:
            return (
                self.referrals.annotate(created_local_tz=TruncDate("created", tzinfo=local_tz))
                .filter(
                    created_local_tz__gte=previous_month_date,
                    created_local_tz__lte=current_month_date,
                )
                .all()
            )

    def get_all_direct_referral_month_count(self):
        return self.get_all_direct_referral_month().count()

    def get_direct_referral_start_month(self):
        local_tz = get_localzone()
        nth_of_the_month = self.created.astimezone(local_tz).day

        current_month_date = timezone.localtime().date() + relativedelta(day=int(nth_of_the_month))
        previous_month_date = current_month_date - relativedelta(months=1, day=int(nth_of_the_month))
        next_month_date = current_month_date + relativedelta(months=1, day=int(nth_of_the_month))

        if int(nth_of_the_month) < int(timezone.localtime().day):
            return current_month_date
        else:
            return previous_month_date

    def get_direct_referral_end_month(self):
        local_tz = get_localzone()
        nth_of_the_month = self.created.astimezone(local_tz).day

        current_month_date = timezone.localtime().date() + relativedelta(day=int(nth_of_the_month))
        previous_month_date = current_month_date - relativedelta(months=1, day=int(nth_of_the_month))
        next_month_date = current_month_date + relativedelta(months=1, day=int(nth_of_the_month))

        if int(nth_of_the_month) < int(timezone.localtime().day):
            return next_month_date
        else:
            return current_month_date

    def __str__(self):
        return "%s" % (self.get_full_name())


class PersonalInfo(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="personal_info")
    birthdate = models.DateField(
        blank=True,
        null=True,
    )
    gender = models.CharField(max_length=6, choices=Gender.choices, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "%s" % (self.account)


class ContactInfo(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="contact_info")
    contact_number = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "%s : %s" % (
            self.account,
            self.contact_number,
        )


class AddressInfo(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="address_info")
    street = models.TextField(
        blank=True,
        null=True,
    )
    city = models.TextField(
        blank=True,
        null=True,
    )
    state = models.TextField(
        blank=True,
        null=True,
    )
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Addresses"

    def __str__(self):
        return "%s" % (self.account)

    def get_full_address(self):
        return "%s %s %s" % (self.street, self.city, self.state)


class AvatarInfo(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="avatar_info")
    file_name = models.CharField(max_length=255, null=True, blank=True)
    file_attachment = models.ImageField(blank=True, upload_to=account_avatar_directory)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "%s : %s - %s" % (
            self.account,
            self.file_attachment,
            self.file_name,
        )
