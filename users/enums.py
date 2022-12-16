from django.db import models
from django.utils.translation import gettext_lazy as _


class UserType(models.TextChoices):
    DEVELOPER = "Developer", _("Developer")
    STAFF = "Staff", _("Staff")
    ADMIN = "Admin", _("Admin")
    MEMBER = "Member", _("Member")
