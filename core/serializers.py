from rest_framework.serializers import ModelSerializer
from rest_framework import serializers
from django.utils import timezone
from core.models import (
    Setting,
    Package,
    ReferralBonus,
    LeadershipBonus,
    Code,
    Activity,
    ActivityDetails,
)
from core.services import generate_code


class SettingsSerializer(ModelSerializer):
    class Meta:
        model = Setting
        fields = ["property", "value"]


class PackagesSerializer(ModelSerializer):
    class Meta:
        model = Package
        fields = [
            "id",
            "package_name",
            "package_amount",
            "has_pairing",
            "point_value",
            "flush_out_limit",
            "is_bco",
        ]


class ReferralBonusesSerializer(ModelSerializer):
    class Meta:
        model = ReferralBonus
        fields = [
            "package_referrer",
            "package_referred",
            "point_value",
        ]


class LeadershipBonusesSerializer(ModelSerializer):
    class Meta:
        model = LeadershipBonus
        fields = [
            "package",
            "level",
            "point_value_percentage",
        ]


class CodesSerializer(ModelSerializer):
    expiration = serializers.CharField(source="get_expiration", required=False)

    class Meta:
        model = Code
        fields = ["code", "package", "code_type", "status", "owner", "is_expiring", "expiration", "created_by"]


class ActivitiesSerializer(ModelSerializer):
    amount = serializers.DecimalField(
        required=False,
        decimal_places=2,
        max_digits=13,
    )
    activity_details = serializers.CharField(source="get_activity_details", required=False)
    account_name = serializers.CharField(source="account.get_account_name", required=False)
    account_number = serializers.CharField(source="account.get_account_number", required=False)

    class Meta:
        model = Activity
        fields = [
            "wallet",
            "account_name",
            "account_number",
            "activity_type",
            "amount",
            "activity_details",
            "created",
            "modified",
        ]


class GenerateCodeSerializer(ModelSerializer):
    quantity = serializers.CharField()

    class Meta:
        model = Code
        fields = "__all__"

    def create(self, validated_data):
        quantity = validated_data.pop("quantity")

        if quantity:
            for i in range(int(quantity)):
                generated_code = generate_code()
                if generated_code:
                    code = Code.objects.create(**validated_data, code=generated_code + "2")
                    code.save()
                return code
