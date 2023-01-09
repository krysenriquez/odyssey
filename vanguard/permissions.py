from typing import Type
from django.http.request import HttpRequest
from rest_framework.permissions import BasePermission
from users.enums import UserType


class IsDeveloperUser(BasePermission):
    def has_permission(self, request: Type[HttpRequest], view):
        if request.user.user_type == UserType.DEVELOPER:
            return bool(request.user and request.user.user_type == UserType.DEVELOPER)
        return False


class IsAdminUser(BasePermission):
    def has_permission(self, request: Type[HttpRequest], view):
        if request.user.user_type == UserType.ADMIN:
            return bool(request.user and request.user.user_type == UserType.ADMIN)
        return False


class IsStaffUser(BasePermission):
    def has_permission(self, request: Type[HttpRequest], view):
        if request.user.user_type == UserType.STAFF:
            return bool(request.user and request.user.user_type == UserType.STAFF)
        return False


class IsMemberUser(BasePermission):
    def has_permission(self, request: Type[HttpRequest], view):
        if request.user.user_type == UserType.MEMBER:
            return bool(request.user and request.user.user_type == UserType.MEMBER)
        return False
