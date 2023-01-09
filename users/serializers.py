from rest_framework.serializers import ModelSerializer
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from accounts.models import Account
from users.models import *


class ResetPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(required=True)
    user = serializers.IntegerField(required=True)

    class Meta:
        model = User
        fields = "__all__"

    def validate_new_password(self, value):
        validate_password(value)
        return value


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
    user = serializers.IntegerField(required=True)

    class Meta:
        model = User
        fields = "__all__"

    def validate_new_password(self, value):
        validate_password(value)
        return value


class ContentTypeSerializer(ModelSerializer):
    class Meta:
        model = ContentType
        fields = "__all__"


class UserLogsDetailsSerializer(ModelSerializer):
    class Meta:
        model = LogDetails
        fields = "__all__"
        read_only_fields = ("logDetails",)


class UserLogsSerializer(ModelSerializer):
    action_type_text = serializers.CharField(read_only=True)
    log_details = UserLogsDetailsSerializer(many=True, required=False)
    username = serializers.CharField(read_only=True)

    def create(self, validated_data):
        logDetails = validated_data.pop("logDetails")
        log = UserLogs.objects.create(**validated_data)

        for detail in logDetails:
            LogDetails.objects.create(**detail, logDetails=log)

        return log

    class Meta:
        model = UserLogs
        fields = "__all__"


class RolePermissionsSerializer(ModelSerializer):
    permission_name = serializers.CharField(source="permission.permission_name", required=False)

    class Meta:
        model = RolePermissions
        fields = [
            "permission_name",
            "can_create",
            "can_retrieve",
            "can_delete",
            "can_update",
        ]


class UserSerializer(ModelSerializer):
    def create(self, validated_data):
        user = User.objects.create(**validated_data)
        user.set_password(validated_data["password"])
        user.save()
        return user

    def update(self, instance, validated_data):
        instance.username = validated_data.get("username", instance.username)
        instance.email_address = validated_data.get("email_address", instance.email_address)
        instance.user_type = validated_data.get("user_type", instance.user_type)
        instance.is_active = validated_data.get("is_active", instance.is_active)
        instance.save()

        return instance

    class Meta:
        model = User
        fields = [
            "username",
            "email_address",
        ]
