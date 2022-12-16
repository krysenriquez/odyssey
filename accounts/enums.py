from django.db import models
from django.utils.translation import gettext_lazy as _


class AccountStatus(models.TextChoices):
    DRAFT = "DRAFT", _("Draft")
    PENDING = "PENDING", _("Pending")
    ACTIVE = "ACTIVE", _("Active")
    DEACTIVATED = "DEACTIVATED", _("Deactivated")
    CLOSED = "CLOSED", _("Closed")


class ParentSide(models.TextChoices):
    LEFT = "LEFT", _("Left")
    RIGHT = "RIGHT", _("Right")


class Gender(models.TextChoices):
    MALE = "MALE", _("Male")
    FEMALE = "FEMALE", _("Female")


class CodeStatus(models.TextChoices):
    ACTIVE = "ACTIVE", _("Active")
    USED = "USED", _("Used")
    EXPIRED = "EXPIRED", _("Expired")
    DEACTIVATED = "DEACTIVATED", _("Deactivated")
