from rest_framework.serializers import ModelSerializer
from rest_framework import serializers
from django.utils import timezone
from .models import *


class PersonalInfoSerializer(ModelSerializer):
    id = serializers.IntegerField(required=False)

    def update(self, instance, validated_data):
        instance.birthdate = validated_data.get("birthdate", instance.birthdate)
        instance.gender = validated_data.get("gender", instance.gender)
        instance.save()

        return instance

    class Meta:
        model = PersonalInfo
        fields = ["id", "birthdate", "gender"]
        read_only_fields = ("account",)


class ContactInfoSerializer(ModelSerializer):
    id = serializers.IntegerField(required=False)

    def update(self, instance, validated_data):
        instance.contact_number = validated_data.get("contact_number", instance.contact_number)
        instance.save()

        return instance

    class Meta:
        model = ContactInfo
        fields = ["id", "contact_number"]
        read_only_fields = ("account",)


class AddressInfoSerializer(ModelSerializer):
    id = serializers.IntegerField(required=False)
    full_address = serializers.CharField(source="get_full_address", required=False)

    def update(self, instance, validated_data):
        instance.street = validated_data.get("street", instance.street)
        instance.city = validated_data.get("city", instance.city)
        instance.state = validated_data.get("state", instance.state)
        instance.save()

        return instance

    class Meta:
        model = AddressInfo
        fields = [
            "id",
            "street",
            "city",
            "state",
            "full_address",
        ]
        read_only_fields = ("account",)


class AvatarInfoSerializer(ModelSerializer):
    id = serializers.IntegerField(required=False)

    def update(self, instance, validated_data):
        instance.file_name = validated_data.get("file_name", instance.file_name)
        instance.file_attachment = validated_data.get("file_attachment", instance.file_attachment)
        instance.save()

        return instance

    class Meta:
        model = AvatarInfo
        fields = [
            "id",
            "file_name",
            "file_attachment",
        ]
        read_only_fields = ("account",)


class AccountSerializer(ModelSerializer):
    id = serializers.IntegerField(required=False)
    personal_info = PersonalInfoSerializer(many=True, required=False)
    contact_info = ContactInfoSerializer(many=True, required=False)
    address_info = AddressInfoSerializer(many=True, required=False)
    avatar_info = AvatarInfoSerializer(many=True, required=False)
    parent_name = serializers.CharField(source="self.parent.get_fullname", required=False)
    referrer_name = serializers.CharField(source="self.referrer.get_fullname", required=False)

    def create(self, validated_data):
        personal_info = validated_data.pop("personal_info")
        contact_info = validated_data.pop("contact_info")
        address_info = validated_data.pop("address_info")
        avatar_info = validated_data.pop("avatar_info")
        account = Account.objects.create(**validated_data)

        for personal in personal_info:
            PersonalInfo.objects.create(**personal, account=account)

        for contact in contact_info:
            ContactInfo.objects.create(**contact, account=account)

        for address in address_info:
            AddressInfo.objects.create(**address, account=account)

        for avatar in avatar_info:
            AvatarInfo.objects.create(**avatar, account=account)

        return account

    def update(self, instance, validated_data):
        personal_info = validated_data.get("personal_info")
        contact_info = validated_data.get("contact_info")
        address_info = validated_data.get("address_info")
        avatar_info = validated_data.get("avatar_info")

        instance.first_name = validated_data.get("first_name", instance.first_name)
        instance.middle_name = validated_data.get("middle_name", instance.middle_name)
        instance.last_name = validated_data.get("last_name", instance.last_name)
        instance.account_status = validated_data.get("account_status", instance.account_status)
        instance.is_deleted = validated_data.get("is_deleted", instance.is_deleted)
        instance.save()

        keep_personal_info = []
        if personal_info:
            for personal in personal_info:
                if "id" in personal.keys():
                    if PersonalInfo.objects.filter(id=personal_info["id"]).exists():
                        e = PersonalInfo.objects.get(id=personal_info["id"])

                        e.save()
                        keep_personal_info.append(e.id)
                    else:
                        continue
                else:
                    e = PersonalInfo.objects.create(**personal, account=instance)
                    keep_personal_info.append(e.id)

            for personal in instance.personal_info.all():
                if personal.id not in keep_personal_info:
                    personal.delete()

        keep_contact_info = []
        if contact_info:
            for contact in contact_info:
                if "id" in contact.keys():
                    if ContactInfo.objects.filter(id=contact_info["id"]).exists():
                        e = ContactInfo.objects.get(id=contact_info["id"])
                        e.contact_number = validated_data.get("contact_number", e.contact_number)
                        e.save()
                        keep_contact_info.append(e.id)
                    else:
                        continue
                else:
                    e = ContactInfo.objects.create(**contact, account=instance)
                    keep_contact_info.append(e.id)

            for contact in instance.contact_info.all():
                if contact.id not in keep_contact_info:
                    contact.delete()

        keep_address_info = []
        if address_info:
            for address in address_info:
                if "id" in address.keys():
                    if AddressInfo.objects.filter(id=address_info["id"]).exists():
                        e = AddressInfo.objects.get(id=address_info["id"])
                        e.street = validated_data.get("street", e.street)
                        e.city = validated_data.get("city", e.city)
                        e.state = validated_data.get("state", e.state)
                        e.save()
                        keep_address_info.append(e.id)
                    else:
                        continue
                else:
                    e = AddressInfo.objects.create(**address, account=instance)
                    keep_address_info.append(e.id)

            for address in instance.address_info.all():
                if address.id not in keep_address_info:
                    address.delete()

        keep_avatar_info = []
        if avatar_info:
            for avatar in avatar_info:
                if "id" in avatar.keys():
                    if AvatarInfo.objects.filter(id=avatar_info["id"]).exists():
                        e = AvatarInfo.objects.get(id=avatar_info["id"])
                        e.file_name = validated_data.get("file_name", e.file_name)
                        e.file_attachment = validated_data.get("file_attachment", e.file_attachment)
                        e.save()
                        keep_avatar_info.append(e.id)
                    else:
                        continue
                else:
                    e = AvatarInfo.objects.create(**avatar, account=instance)
                    keep_avatar_info.append(e.id)

            for avatar in instance.avatar_info.all():
                if avatar.id not in keep_avatar_info:
                    avatar.delete()

    class Meta:
        model = Account
        fields = "__all__"


class AccountProfileSerializer(ModelSerializer):
    personal_info = PersonalInfoSerializer(many=True, required=False)
    contact_info = ContactInfoSerializer(many=True, required=False)
    address_info = AddressInfoSerializer(many=True, required=False)
    avatar_info = AvatarInfoSerializer(many=True, required=False)
    parent_name = serializers.CharField(source="self.parent.get_fullname", required=False)
    referrer_name = serializers.CharField(source="self.referrer.get_fullname", required=False)
    full_name = serializers.CharField(source="get_full_name", required=False)
    account_number = serializers.CharField(source="get_account_number", required=False)

    def get_avatar_info(self, obj):
        return obj.avatar_info[0]["file_attachment"]

    class Meta:
        model = Account
        fields = "__all__"


class AccountListSerializer(ModelSerializer):
    account_name = serializers.CharField(source="get_account_name", required=False)
    account_number = serializers.CharField(source="get_account_number", required=False)
    account_package = serializers.CharField(source="get_account_package", required=False)
    account_package_amount = serializers.CharField(source="get_account_package_amount", required=False)
    parent_account_name = serializers.CharField(source="parent.get_account_name", required=False)
    parent_account_number = serializers.CharField(source="parent.get_account_number", required=False)
    referrer_account_name = serializers.CharField(source="referrer.get_account_name", required=False)
    referrer_account_number = serializers.CharField(source="referrer.get_account_number", required=False)

    class Meta:
        model = Account
        fields = [
            "account_id",
            "account_name",
            "account_number",
            "account_package",
            "account_package_amount",
            "parent_account_name",
            "parent_account_number",
            "referrer_account_name",
            "referrer_account_number",
            "account_status",
            "created",
        ]


class AccountReferralsSerializer(ModelSerializer):
    account_name = serializers.CharField(source="get_account_name", required=False)
    account_number = serializers.CharField(source="get_account_number", required=False)
    referrals = serializers.IntegerField(source="get_all_direct_referral_count", required=False)

    class Meta:
        model = Account
        fields = [
            "account_id",
            "account_name",
            "account_number",
            "referrals",
        ]


class AccountWalletSerializer(ModelSerializer):
    account_name = serializers.CharField(source="get_account_name", required=False)
    account_number = serializers.CharField(source="get_account_number", required=False)
    wallet_amount = serializers.CharField(read_only=True)

    class Meta:
        model = Account
        fields = [
            "account_name",
            "account_number",
            "wallet_amount",
        ]


class AvatarInfoSerializer(ModelSerializer):
    class Meta:
        model = AvatarInfo
        fields = ["file_attachment"]


# Imported to User App
class AccountAvatarSerializer(ModelSerializer):
    avatar_info = AvatarInfoSerializer(many=True, required=False)
    account_name = serializers.CharField(read_only=True)
    account_number = serializers.CharField(source="get_account_number", required=False)

    class Meta:
        model = Account
        fields = ["account_id", "account_name", "account_number", "avatar_info"]


class GenealogyAvatarSerializer(ModelSerializer):
    class Meta:
        model = AvatarInfo
        fields = ["file_attachment"]


class RecursiveField(serializers.BaseSerializer):
    def to_representation(self, value):
        parent = self.parent
        if isinstance(parent, serializers.ListSerializer):
            parent = parent.parent

        depth = getattr(parent, "depth", 1)
        ParentSerializer = self.parent.parent.__class__
        serializer = ParentSerializer(value, context=self.context)
        serializer.depth = depth + 1
        return serializer.data

    def to_internal_value(self, data):
        ParentSerializer = self.parent.parent.__class__
        try:
            instance = Account.objects.get(pk=data)
        except Account.DoesNotExist:
            raise serializers.ValidationError("Account {0} does not exists".format(Account().__class__.__name__))
        return instance


class GenealogyAccountSerializer(ModelSerializer):
    avatar_info = GenealogyAvatarSerializer(many=True, required=False)
    account_name = serializers.CharField(source="get_account_name", required=False)
    account_number = serializers.CharField(source="get_account_number", required=False)
    all_left_children_count = serializers.CharField(read_only=True)
    all_right_children_count = serializers.CharField(read_only=True)
    depth = serializers.SerializerMethodField()

    def __init__(self, *args, depth=0, **kwargs):
        super().__init__(*args, **kwargs)
        self.depth = depth

    def get_depth(self, obj):
        return self.depth

    def get_fields(self):
        fields = super().get_fields()
        if self.depth < 5:
            fields["children"] = RecursiveField(many=True, required=False)
        else:
            del fields["children"]

        return fields

    class Meta:
        model = Account
        ordering = ("parent_side",)
        fields = [
            "account_id",
            "account_name",
            "account_number",
            "account_status",
            "parent_side",
            "depth",
            "avatar_info",
            "children",
            "all_left_children_count",
            "all_right_children_count",
        ]


class BinaryAccountProfileParentSerializer(ModelSerializer):
    avatar_info = GenealogyAvatarSerializer(many=True, required=False)
    account_name = serializers.CharField(source="get_account_name", required=False)
    account_number = serializers.CharField(source="get_account_number", required=False)

    class Meta:
        model = Account
        ordering = ("parent_side",)
        fields = [
            "account_id",
            "account_name",
            "account_number",
            "account_status",
            "avatar_info",
        ]


class BinaryAccountProfileSerializer(ModelSerializer):
    avatar_info = GenealogyAvatarSerializer(many=True, required=False)
    account_name = serializers.CharField(source="get_account_name", required=False)
    account_number = serializers.CharField(source="get_account_number", required=False)
    all_left_children_count = serializers.CharField(read_only=True)
    all_right_children_count = serializers.CharField(read_only=True)
    parent = BinaryAccountProfileParentSerializer(required=False)
    referrer = BinaryAccountProfileParentSerializer(required=False)

    def __init__(self, *args, depth=0, **kwargs):
        super().__init__(*args, **kwargs)
        self.depth = depth

    def get_fields(self):
        fields = super().get_fields()
        if self.depth < 1:
            fields["children"] = RecursiveField(many=True, required=False)
        else:
            del fields["parent"]
            del fields["children"]

        return fields

    class Meta:
        model = Account
        ordering = ("parent_side",)
        fields = [
            "account_id",
            "account_name",
            "account_number",
            "account_status",
            "parent_side",
            "avatar_info",
            "children",
            "all_left_children_count",
            "all_right_children_count",
            "parent",
            "referrer",
        ]
