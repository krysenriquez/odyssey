from django.db import models
from django.utils.translation import gettext_lazy as _

# Core Settings
class CodeType(models.TextChoices):
    ACTIVATION = "ACTIVATION", _("Activation")
    UPGRADE = "UPGRADE", _("Upgrade")
    REACTIVATION = "REACTIVATION", _("Reactivation")
    FREE_SLOT = "FREE_SLOT", _("Free Slot")


class CodeStatus(models.TextChoices):
    ACTIVE = "ACTIVE", _("Active")
    USED = "USED", _("Used")
    EXPIRED = "EXPIRED", _("Expired")
    DEACTIVATED = "DEACTIVATED", _("Deactivated")


class Settings(models.TextChoices):
    CODE_EXPIRATION = "CODE_EXPIRATION", _("Code Expiration")
    POINT_VALUE_CONVERSION = "POINT_VALUE_CONVERSION", _("Point Value Conversion")
    FLUSH_OUT_PENALTY_PERCENTAGE_WEAK = "FLUSH_OUT_PENALTY_PERCENTAGE_WEAK", _("Flush Out Penalty Weak Percentage Leg")
    FLUSH_OUT_PENALTY_PERCENTAGE_STRONG = "FLUSH_OUT_PENALTY_PERCENTAGE_STRONG", _(
        "Flush Out Penalty Strong Percentage Leg"
    )
    DIRECT_REFERRAL_PERCENTAGE = "DIRECT_REFERRAL_PERCENTAGE", _("Direct Referral Percentage")
    REFERRAL_BONUS_COUNT = "REFERRAL_BONUS_COUNT", _("Referral Program Count")
    FRANCHISE_COMMISSION_PERCENTAGE = "FRANCHISE_COMMISSION_PERCENTAGE", _("Franchise Commission Percentage")
    GLOBAL_POOL_BONUS_PERCENTAGE = "GLOBAL_POOL_BONUS_PERCENTAGE", _("Global Pool Bonus Percentage")
    GLOBAL_POOL_BONUS_REQUIREMENT = "GLOBAL_POOL_BONUS_REQUIREMENT", _("Global Pool Bonus Requirement")
    COMPANY_CASHOUT_FEE_PERCENTAGE = "COMPANY_CASHOUT_FEE_PERCENTAGE", _("Company Cashout Fee Percentage")
    B_WALLET_CASHOUT_DAY = "B_WALLET_CASHOUT_DAY", _("Binary Wallet Cashout Day")
    B_WALLET_CASHOUT_OVERRIDE = "B_WALLET_CASHOUT_OVERRIDE", _("Binary Wallet Cashout Override")
    F_WALLET_CASHOUT_DAY = "F_WALLET_CASHOUT_DAY", _("Franchise Wallet Cashout Day")
    F_WALLET_CASHOUT_OVERRIDE = "F_WALLET_CASHOUT_OVERRIDE", _("Franchise Wallet Cashout Override")
    MAX_USER_ACCOUNT_LIMIT = "MAX_USER_ACCOUNT_LIMIT", _("Max User Account Limit")
    CODE_LENGTH = "CODE_LENGTH", _("Code Length")


# Core Activities
class ActivityType(models.TextChoices):
    # * --- C Wallet
    ENTRY = "ENTRY", _("Entry")  # * No Foreign Key to New Member Account
    FRANCHISE_ENTRY = "FRANCHISE_ENTRY", _("Franchise Entry")  # * No Foreign Key to New Member Account
    PAYOUT = "PAYOUT", _("Payout")  # * Foreign Key to Cashout
    COMPANY_TAX = "COMPANY_TAX", _("Company Tax")  # * Foreign Key to Cashout
    # * --- B Wallet
    DIRECT_REFERRAL = "DIRECT_REFERRAL", _("Direct Referral")  # * Foreign Key to Sponsored Account
    SALES_MATCH = "SALES_MATCH", _("Sales Match")
    REFERRAL_BONUS = "REFERRAL_BONUS", _("Referral Bonus")
    GLOBAL_POOL_BONUS = "GLOBAL_POOL_BONUS", _("Global Pool Bonus")
    # * --- F Wallet
    FRANCHISE_COMMISSION = "FRANCHISE_COMMISSION", _("Franchise Commission")  # * Foreign Key to Sponsored Account
    # * --- B and F Wallet
    CASHOUT = "CASHOUT", _("Cashout")  # * Foreign Key to Cashout
    # * --- PV Left and Right Wallet
    DOWNLINE_ENTRY = "DOWNLINE_ENTRY", _("Downline Entry")
    PV_SALES_MATCH = "PV_SALES_MATCH", _("Point Value Sales Match")
    LEADERSHIP_BONUS = "LEADERSHIP_BONUS", _("Leadership Bonus")
    FLUSH_OUT_PENALTY = "FLUSH_OUT_PENALTY", _("Flush Out Penalty")


class ActivityStatus(models.TextChoices):
    REQUESTED = "REQUESTED", _("Requested")
    APPROVED = "APPROVED", _("Approved")
    RELEASED = "RELEASED", _("Released")
    DENIED = "DENIED", _("Denied")
    DONE = "DONE", _("Done")


class WalletType(models.TextChoices):
    C_WALLET = "C_WALLET", _("Company Wallet")
    B_WALLET = "B_WALLET", _("Binary Wallet")
    F_WALLET = "F_WALLET", _("Franchise Wallet")
    # Sub Wallets for Pairing
    PV_LEFT_WALLET = "PV_LEFT_WALLET", _("Point Value Left Wallet")
    PV_RIGHT_WALLET = "PV_RIGHT_WALLET", _("Point Value Right Wallet")
    PV_TOTAL_WALLET = "PV_TOTAL_WALLET", _("Point Value Total Wallet")


class CashoutMethod(models.TextChoices):
    GCASH = "GCash", _("GCash")
    CEBUANA = "Cebuana", _("Cebuana")
    PALAWAN_EXPRESS = "Palawan Express", _("Palawan Express")
    UNION_BANK = "Union Bank", _("Union Bank")
    BDO = "BDO", _("BDO")
