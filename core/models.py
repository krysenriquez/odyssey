import datetime
from django.db import models
from django.utils import timezone
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from tzlocal import get_localzone
from accounts.enums import Gender
from accounts.models import Account
from core.enums import CodeType, Settings
from core.enums import Settings, CodeStatus, CodeType, ActivityType, ActivityStatus, WalletType

# Core Settings
class Setting(models.Model):
    property = models.CharField(max_length=255, default=None, choices=Settings.choices)
    value = models.DecimalField(default=0, max_length=256, decimal_places=2, max_digits=13, blank=True, null=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return "%s - %s" % (self.property, self.value)


class Package(models.Model):
    package_name = models.CharField(max_length=255, null=True, blank=True)
    package_amount = models.DecimalField(
        default=0, max_length=256, decimal_places=2, max_digits=13, blank=True, null=True
    )
    has_pairing = models.BooleanField(
        default=True,
    )
    point_value = models.DecimalField(default=0, max_length=256, decimal_places=2, max_digits=13, blank=True, null=True)
    flush_out_limit = models.DecimalField(
        default=0, max_length=256, decimal_places=2, max_digits=13, blank=True, null=True
    )
    is_franchise = models.BooleanField(
        default=False,
    )
    is_bco = models.BooleanField(
        default=False,
    )
    created_by = models.ForeignKey("users.User", on_delete=models.SET_NULL, related_name="created_package", null=True)

    def __str__(self):
        return "%s: %s - %s PV" % (self.package_name, self.package_amount, self.point_value)


# To be retrieved once Referral Program Count is reached
class ReferralBonus(models.Model):
    package_referrer = models.ForeignKey(
        Package, on_delete=models.CASCADE, related_name="referral_bonus_package_referrer"
    )
    package_referred = models.ForeignKey(
        Package, on_delete=models.CASCADE, related_name="referral_bonus_package_referred"
    )
    point_value = models.DecimalField(default=0, max_length=256, decimal_places=2, max_digits=13, blank=True, null=True)
    created_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        related_name="created_referral_bonus",
        null=True,
    )

    def __str__(self):
        return "%s - %s : %s PV" % (
            self.package_referrer.package_name,
            self.package_referred.package_name,
            self.point_value,
        )


# Real Time Bonus once downline has incurred an Activity
class LeadershipBonus(models.Model):
    package = models.ForeignKey(Package, on_delete=models.CASCADE, related_name="leadership_bonus_package")
    level = models.DecimalField(default=0, max_length=256, decimal_places=2, max_digits=13, blank=True, null=True)
    point_value_percentage = models.DecimalField(
        default=0, max_length=256, decimal_places=2, max_digits=13, blank=True, null=True
    )
    created_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        related_name="created_leadership_bonus",
        null=True,
    )

    def __str__(self):
        return "%s: %s - %s" % (self.package.package_name, self.level, self.point_value_percentage)


class Code(models.Model):
    code = models.CharField(max_length=30, null=True, blank=True)
    package = models.ForeignKey(Package, on_delete=models.CASCADE, null=True, blank=True, related_name="code")
    code_type = models.CharField(max_length=32, choices=CodeType.choices, default=CodeType.ACTIVATION)
    status = models.CharField(max_length=32, choices=CodeStatus.choices, default=CodeStatus.ACTIVE)
    owner = models.ForeignKey(
        "accounts.Account", on_delete=models.CASCADE, null=True, blank=True, related_name="codes_owned"
    )
    created_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        related_name="created_code",
        null=True,
    )
    is_expiring = models.BooleanField(
        default=False,
    )
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    deleted = models.DateTimeField(blank=True, null=True)
    is_deleted = models.BooleanField(
        default=False,
    )

    def __str__(self):
        return "%s - %s - %s - %s : %s" % (
            self.code,
            self.package,
            self.code_type,
            self.owner,
            self.status,
        )

    def get_has_owner(self):
        return bool(self.owner)

    def update_status(self, classmodel):
        object = classmodel.objects.get(activation_code=self)
        if object:
            if self.status == CodeStatus.ACTIVE:
                self.status = CodeStatus.USED
                self.save()

    def activate_deactivate(self):
        if self.status == CodeStatus.ACTIVE:
            self.status = CodeStatus.DEACTIVATED
            self.save()
            return True

        if self.status == CodeStatus.DEACTIVATED:
            self.status = CodeStatus.ACTIVE
            self.save()
            return True

        return False

    def get_expiration(self):
        if self.status == CodeStatus.ACTIVE and self.is_expiring == True:
            code_expiration = int(Setting.objects.get(property=Settings.CODE_EXPIRATION).value)
            local_tz = get_localzone()
            modified = self.modified.astimezone(local_tz)
            expiry = modified + datetime.timedelta(hours=code_expiration)
            if timezone.localtime() > expiry:
                self.status = CodeStatus.EXPIRED
                self.save()
                return CodeStatus.EXPIRED
            else:
                time_diff = expiry - timezone.localtime()
                td = datetime.timedelta(seconds=time_diff.total_seconds())
                return "%02d:%02d:%02d" % (
                    td.days * 24 + td.seconds // 3600,
                    (td.seconds // 60) % 60,
                    td.seconds % 60,
                )
        elif self.is_expiring == False:
            return "Non-Expiring Code"
        else:
            return "00:00:00"


class Activity(models.Model):
    account = models.ForeignKey(
        "accounts.Account",
        on_delete=models.SET_NULL,
        related_name="activity",
        null=True,
        blank=True,
    )
    activity_type = models.CharField(max_length=32, choices=ActivityType.choices, blank=True, null=True)
    activity_amount = models.DecimalField(
        default=0, max_length=256, decimal_places=2, max_digits=13, blank=True, null=True
    )
    status = models.CharField(
        max_length=32,
        choices=ActivityStatus.choices,
        default=ActivityStatus.REQUESTED,
    )
    wallet = models.CharField(max_length=32, choices=WalletType.choices, blank=True, null=True)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name="activity_content_type",
        blank=True,
        null=True,
    )
    object_id = models.PositiveIntegerField(
        blank=True,
        null=True,
    )
    content_object = GenericForeignKey(
        "content_type",
        "object_id",
    )
    created_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        related_name="created_activity",
        null=True,
    )
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    deleted = models.DateTimeField(blank=True, null=True)
    is_deleted = models.BooleanField(
        default=False,
    )
    note = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name_plural = "Activities"

    def __str__(self):
        return "%s : %s : %s - %s" % (self.activity_type, self.wallet, self.activity_amount, self.account)

    def get_activity_number(self):
        return str(self.id).zfill(7)

    def get_activity_summary(self):
        detail = []
        if self.content_type:
            generic_object = self.content_type.model_class().objects.get(id=self.object_id)
            match self.activity_type:
                case ActivityType.ENTRY:
                    detail = "Entry on %s" % (str(generic_object.pk).zfill(5))
                case ActivityType.FRANCHISE_ENTRY:
                    detail = "Franchise Entry on %s" % (str(generic_object.pk).zfill(5))
                case ActivityType.PAYOUT:
                    detail = "Payout to Cashout %s" % (str(generic_object.pk).zfill(5))
                case ActivityType.COMPANY_TAX:
                    detail = "Received from Cashout %s" % (str(generic_object.pk).zfill(5))
                case ActivityType.DIRECT_REFERRAL:
                    detail = "Direct Referral on %s" % (str(generic_object.pk).zfill(5))
                case ActivityType.SALES_MATCH:
                    detail = "Sales Match"
                case ActivityType.LEADERSHIP_BONUS:
                    detail = "Leadership Bonus"
                case ActivityType.FRANCHISE_COMMISSION:
                    detail = "Franchise Commission on %s" % (str(generic_object.pk).zfill(5))
                case ActivityType.FIFTH_PAIR:
                    detail = "Reached Fifth Pairing"
                case ActivityType.DOWNLINE_ENTRY:
                    detail = "Downline Entry on %s" % (str(generic_object.pk).zfill(5))
                case ActivityType.CASHOUT:
                    detail = "Cashout"
        else:
            match self.activity_type:
                case ActivityType.REFERRAL_BONUS:
                    detail = "Reached 2 Referrals of Same Package"
                case ActivityType.GLOBAL_POOL_BONUS:
                    detail = "Transferred Global Pool Bonus"

        return "%s" % (detail)

    def get_content_type_model(self):
        return "%s" % (self.content_type.model)

    def get_cashout_number(self):
        return str(self.id).zfill(5)


class ActivityDetails(models.Model):
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name="details")
    action = models.CharField(
        max_length=255,
    )
    created_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        related_name="created_activity_details",
        null=True,
    )
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "%s - %s" % (self.activity, self.action)


class Franchisee(models.Model):
    activation_code = models.ForeignKey(
        "core.Code",
        related_name="franchisee_activated",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    package = models.ForeignKey(
        "core.Package",
        related_name="franchisee",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    referrer = models.ForeignKey(
        "accounts.Account",
        related_name="franchisee_referrals",
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
    gender = models.CharField(max_length=6, choices=Gender.choices, blank=True, null=True)
    email_address = models.CharField(max_length=255, null=True, blank=True)
    contact_number = models.CharField(max_length=255, null=True, blank=True)
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
    created_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        related_name="created_franchisee",
        null=True,
    )
    created = models.DateTimeField(auto_now_add=True)

    def get_full_name(self):
        return "%s %s %s" % (self.first_name, self.middle_name, self.last_name)

    def __str__(self):
        return "%s" % (self.get_full_name())
