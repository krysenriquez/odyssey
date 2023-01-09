from django.contrib import admin
from core.models import Setting, Package, ReferralBonus, LeadershipBonus, Code, Activity, ActivityDetails, Franchisee


class ActivityAdmin(admin.ModelAdmin):
    list_display = ("activity_type", "account", "activity_amount", "wallet", "created", "modified")
    search_fields = ("account__id",)
    list_filter = ("activity_type", "wallet")
    ordering = ("-modified",)

    class Meta:
        model = Activity
        verbose_name_plural = "Activities"


admin.site.register(Setting)
admin.site.register(Package)
admin.site.register(ReferralBonus)
admin.site.register(LeadershipBonus)
admin.site.register(Code)
admin.site.register(Activity, ActivityAdmin)
admin.site.register(ActivityDetails)
admin.site.register(Franchisee)
