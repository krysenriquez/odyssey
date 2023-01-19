from django import forms
from django.contrib import admin
from django.contrib.admin.models import LogEntry
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from users.models import *


class UserCreationForm(forms.ModelForm):
    password = forms.CharField(label="Password", widget=forms.PasswordInput)
    password_confirm = forms.CharField(label="Password confirmation", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ("username", "email_address")

    def clean_password2(self):
        password = self.cleaned_data.get("password")
        password_confirm = self.cleaned_data.get("password_confirm")
        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError("Passwords don't match")
        return password_confirm

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


class UserChangeForm(forms.ModelForm):

    password = ReadOnlyPasswordHashField(
        label=("Password"),
        help_text=(
            "Raw passwords are not stored, so there is no way to see "
            "this user's password, but you can change the password "
            'using <a href="../password/">this form</a>.'
        ),
    )

    class Meta:
        model = User
        fields = ("username", "email_address", "password", "user_type", "is_active")

    def clean_password(self):
        return self.initial["password"]


class UserAdmin(BaseUserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    model = User

    list_display = ("username", "email_address", "is_active", "is_staff", "is_superuser")
    list_filter = ("is_staff", "is_active", "user_type")
    fieldsets = (
        (None, {"fields": ("username", "email_address", "password")}),
        (
            "Permissions",
            {
                "fields": (
                    "user_type",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "user_permissions",
                    "can_change_username",
                    "can_change_email_address",
                    "can_change_password",
                )
            },
        ),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "username",
                    "email_address",
                    "password",
                    "password_confirm",
                ),
            },
        ),
    )
    search_fields = (
        "username",
        "email_address",
    )
    ordering = (
        "-id",
        "username",
        "email_address",
    )
    filter_horizontal = ()


class RolePermissionsAdmin(admin.ModelAdmin):
    list_display = (
        "user_type",
        "permission",
        "can_create",
        "can_retrieve",
        "can_delete",
        "can_update",
    )
    list_filter = ("user_type", "permission")
    search_fields = (
        "user_type",
        "permission",
    )
    ordering = (
        "id",
        "user_type",
        "permission",
    )
    filter_horizontal = ()

    class Meta:
        model = RolePermissions


users_models = [UserLogs, LogDetails]
admin.site.register(LogEntry)
admin.site.unregister(Group)
admin.site.register(User, UserAdmin)
admin.site.register(Permission)
admin.site.register(RolePermissions, RolePermissionsAdmin)
admin.site.register(users_models)
