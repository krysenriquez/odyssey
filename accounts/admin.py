from django.contrib import admin
from accounts.models import (
    Account,
    PersonalInfo,
    ContactInfo,
    AddressInfo,
    AvatarInfo,
    CashoutMethod
)

admin.site.register(Account)
admin.site.register(PersonalInfo)
admin.site.register(ContactInfo)
admin.site.register(AddressInfo)
admin.site.register(AvatarInfo)
admin.site.register(CashoutMethod)
