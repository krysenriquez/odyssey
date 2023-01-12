from rest_framework.serializers import ModelSerializer
from rest_framework import serializers
from django.utils import timezone
from core.models import (
    Franchisee,
    Setting,
    Package,
    ReferralBonus,
    LeadershipBonus,
    Code,
    Activity,
    ActivityDetails,
)
from core.services import generate_code, get_cashout_total_tax
from accounts.models import Account, CashoutMethod
from accounts.serializers import AccountProfileSerializer, CashoutMethodSerializer


class ContentObjectRelatedField(serializers.RelatedField):
    def to_representation(self, value):
        if isinstance(value, Account):
            serializer = AccountProfileSerializer(value)
        elif isinstance(value, CashoutMethod):
            serializer = CashoutMethodSerializer(value)
        elif isinstance(value, Activity):
            serializer = ActivitiesSerializer(value)
        else:
            raise Exception("Unexpected type of content object")

        return serializer.data


class SettingsSerializer(ModelSerializer):
    class Meta:
        model = Setting
        fields = ["id", "property", "value"]


class PackagesSerializer(ModelSerializer):
    class Meta:
        model = Package
        fields = [
            "id",
            "package_name",
            "package_amount",
            "has_pairing",
            "is_franchise",
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
    owner_name = serializers.CharField(source="owner.get_full_name", required=False)
    owner_account_number = serializers.CharField(source="owner.get_account_number", required=False)
    expiration = serializers.CharField(source="get_expiration", required=False)
    package_name = serializers.CharField(source="package.package_name", required=False)
    is_owned = serializers.CharField(source="get_has_owner", required=False)

    class Meta:
        model = Code
        fields = [
            "code",
            "package_name",
            "owner_name",
            "owner_account_number",
            "code_type",
            "status",
            "is_owned",
            "is_expiring",
            "expiration",
            "created_by",
        ]


class ActivityDetailsSerializer(ModelSerializer):
    created_by_username = serializers.CharField(source="created_by.username", required=False)

    class Meta:
        model = ActivityDetails
        fields = ["action", "created_by_username", "created", "created_by"]
        read_only_fields = ("activity",)


class ActivitiesSerializer(ModelSerializer):
    details = ActivityDetailsSerializer(many=True, required=False)
    activity_summary = serializers.CharField(source="get_activity_summary", required=False)
    account_name = serializers.CharField(source="account.get_full_name", required=False)
    account_number = serializers.CharField(source="account.get_account_number", required=False)
    activity_number = serializers.CharField(source="get_activity_number", required=False)

    class Meta:
        model = Activity
        fields = [
            "activity_number",
            "wallet",
            "account_name",
            "account_number",
            "activity_type",
            "activity_amount",
            "activity_summary",
            "created",
            "modified",
            "status",
            "details",
        ]


class ActivityCashoutListSerializer(ModelSerializer):
    activity_number = serializers.CharField(source="get_activity_number", required=False)
    account_name = serializers.CharField(source="account.get_full_name", required=False)
    account_number = serializers.CharField(source="account.get_account_number", required=False)

    def retrieve_activity_amount_total(self, activity_amount):
        total_tax = (100 - get_cashout_total_tax()) / 100
        return "{:.2f}".format(activity_amount * total_tax)

    def retrieve_activity_amount_tax(self, activity_amount):
        total_tax = get_cashout_total_tax() / 100
        return "{:.2f}".format(activity_amount * total_tax)

    def retrieve_company_tax(self):
        total_tax = get_cashout_total_tax()
        return "{:.2f}".format(total_tax)

    def to_representation(self, instance):
        activity_amount_total = self.retrieve_activity_amount_total(instance.activity_amount)
        activity_amount_total_tax = self.retrieve_activity_amount_tax(instance.activity_amount)
        company_earning_tax = self.retrieve_company_tax()
        data = super(ActivityCashoutListSerializer, self).to_representation(instance)
        data.update(
            {
                "activity_amount_total": activity_amount_total,
                "company_earning_tax": company_earning_tax,
                "activity_amount_total_tax": activity_amount_total_tax,
            }
        )

        return data

    class Meta:
        model = Activity
        fields = [
            "activity_number",
            "activity_amount",
            "account_name",
            "account_number",
            "wallet",
            "status",
            "created",
        ]


class ActivityCashoutInfoSerializer(ModelSerializer):
    details = ActivityDetailsSerializer(many=True, required=False)
    activity_summary = serializers.CharField(source="get_activity_summary", required=False)
    account_name = serializers.CharField(source="account.get_full_name", required=False)
    account_number = serializers.CharField(source="account.get_account_number", required=False)
    activity_number = serializers.CharField(source="get_activity_number", required=False)
    content_object = ContentObjectRelatedField(queryset=Activity.objects.all())

    def retrieve_activity_amount_total(self, activity_amount):
        total_tax = (100 - get_cashout_total_tax()) / 100
        return "{:.2f}".format(activity_amount * total_tax)

    def retrieve_activity_amount_tax(self, activity_amount):
        total_tax = get_cashout_total_tax() / 100
        return "{:.2f}".format(activity_amount * total_tax)

    def retrieve_company_tax(self):
        total_tax = get_cashout_total_tax()
        return "{:.2f}".format(total_tax)

    def to_representation(self, instance):
        activity_amount_total = self.retrieve_activity_amount_total(instance.activity_amount)
        activity_amount_total_tax = self.retrieve_activity_amount_tax(instance.activity_amount)
        company_earning_tax = self.retrieve_company_tax()
        data = super(ActivityCashoutInfoSerializer, self).to_representation(instance)
        data.update(
            {
                "activity_amount_total": activity_amount_total,
                "company_earning_tax": company_earning_tax,
                "activity_amount_total_tax": activity_amount_total_tax,
            }
        )

        return data

    class Meta:
        model = Activity
        fields = [
            "activity_number",
            "wallet",
            "account_name",
            "account_number",
            "activity_type",
            "activity_amount",
            "note",
            "activity_summary",
            "created",
            "modified",
            "status",
            "details",
            "content_object",
        ]


class GenerateCodeSerializer(ModelSerializer):
    class Meta:
        model = Code
        fields = "__all__"

    def create(self, validated_data):
        generated_code = generate_code()
        if generated_code:
            code = Code.objects.create(**validated_data, code=generated_code)
            code.save()
            return code


class CreateActivitiesSerializer(ModelSerializer):
    details = ActivityDetailsSerializer(many=True, required=False)

    def create(self, validated_data):
        details = validated_data.pop("details")
        activity = Activity.objects.create(**validated_data)

        for detail in details:
            ActivityDetails.objects.create(**detail, activity=activity)

        return activity

    def update(self, instance, validated_data):
        details = validated_data.get("details")

        instance.status = validated_data.get("status", instance.status)
        instance.is_deleted = validated_data.get("is_deleted", instance.is_deleted)
        instance.note = validated_data.get("note", instance.note)
        instance.save()

        if details:
            for detail in details:
                ActivityDetails.objects.create(**detail, activity=instance)

        return instance

    class Meta:
        model = Activity
        fields = "__all__"


# Franchise
class FranchiseeListSerializer(ModelSerializer):
    full_name = serializers.CharField(source="get_full_name", required=False)
    referrer_account_name = serializers.CharField(source="referrer.get_full_name", required=False)
    referrer_account_number = serializers.CharField(source="referrer.get_account_number", required=False)
    package_name = serializers.CharField(source="package.package_name", required=False)
    package_amount = serializers.CharField(source="package.package_amount", required=False)
    created_by_username = serializers.CharField(source="created_by.username", required=False)

    class Meta:
        model = Franchisee
        fields = [
            "full_name",
            "referrer_account_name",
            "referrer_account_number",
            "package_name",
            "package_amount",
            "created_by_username",
            "created",
        ]


class CreateFranchiseeSerializer(ModelSerializer):
    def create(self, validated_data):
        franchisee = Franchisee.objects.create(**validated_data)
        return franchisee

    class Meta:
        model = Franchisee
        fields = "__all__"
