import uuid
from django.db import models
from django.contrib.auth.models import (
    AbstractUser,
    BaseUserManager,
)
from django.contrib.contenttypes.fields import (
    GenericForeignKey,
)
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _
from users.enums import UserType


class UserManager(BaseUserManager):
    def _create_user(self, username, email_address, password, **extra_fields):
        if not email_address and not username:
            raise ValueError("A username or email is required to create an account")

        email_address = self.normalize_email(email_address)
        username = self.model.normalize_username(username)

        user = self.model(username=username, email_address=email_address, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email_address, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("user_type", UserType.DEVELOPER)

        email_address = self.normalize_email(email_address)
        username = self.model.normalize_username(username)

        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("Superuser must have is_staff=True."))
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("Superuser must have is_superuser=True."))

        return self._create_user(username, email_address, password, **extra_fields)

    def create_staffuser(self, username, email_address, password, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("user_type", UserType.STAFF)

        email_address = self.normalize_email(email_address)
        username = self.model.normalize_username(username)

        return self._create_user(username, email_address, password, **extra_fields)

    def create_memberuser(self, username, email_address, password, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("user_type", UserType.MEMBER)

        email_address = self.normalize_email(email_address)
        username = self.model.normalize_username(username)

        return self._create_user(username, email_address, password, **extra_fields)


class User(AbstractUser):
    user_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    username = models.CharField(
        unique=True,
        max_length=30,
    )
    email_address = models.EmailField(
        verbose_name="email address",
        max_length=50,
        unique=True,
    )
    user_type = models.CharField(
        max_length=10,
        choices=UserType.choices,
        default=UserType.MEMBER,
    )
    is_active = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    objects = UserManager()

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = [
        "email_address",
    ]

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")

    def __str__(self):
        if not self.username:
            return "%s" % (self.email_address)
        else:
            return "%s" % (self.username)

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True

    def get_all_user_accounts(self):
        accounts = []
        for account in self.account_user.all():
            accounts.append(account)
        return accounts

    def update_is_active(self):
        self.is_active = not self.is_active
        self.save()
        return True


class UserLogs(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_logs")
    action_type = models.CharField(max_length=255, blank=True, null=True)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name="user_logs_content_type",
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
    object_type = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )
    api_link = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )
    value_to_display = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )
    created = models.DateTimeField(
        auto_now_add=True,
    )

    def __str__(self):
        return "%s - %s %s %s" % (
            self.user,
            self.action_type,
            self.content_type,
            self.object_id,
        )


class LogDetails(models.Model):
    user_logs = models.ForeignKey(UserLogs, on_delete=models.CASCADE, related_name="log_details")
    action = models.CharField(
        max_length=255,
    )

    def __str__(self):
        return "%s - %s" % (self.user_logs, self.action)


class Permission(models.Model):
    permission_name = models.CharField(
        max_length=255,
    )

    def __str__(self):
        return "%s" % (self.permission_name)


class RolePermissions(models.Model):
    user_type = models.CharField(
        max_length=10,
        choices=UserType.choices,
        default=UserType.MEMBER,
    )
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE, related_name="roles")
    can_create = models.BooleanField(default=False)
    can_retrieve = models.BooleanField(default=False)
    can_delete = models.BooleanField(default=False)
    can_update = models.BooleanField(default=False)

    def __str__(self):
        return "%s : %s : %s %s %s %s" % (
            self.user_type,
            self.permission,
            self.can_create,
            self.can_retrieve,
            self.can_delete,
            self.can_update,
        )
