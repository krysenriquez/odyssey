from django_cron import CronJobBase, Schedule
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from django.db.models import Q
import datetime
from tzlocal import get_localzone
from django.utils import timezone


class DeleteBlacklistedTokens(CronJobBase):
    RUN_EVERY_MINS = 1
    RETRY_AFTER_FAILURE_MINS = 1
    schedule = Schedule(run_every_mins=RUN_EVERY_MINS, retry_after_failure_mins=RETRY_AFTER_FAILURE_MINS)
    code = "vanguard.delete_blacklisted_tokens"

    def do(self):
        local_tz = get_localzone()
        date_today = datetime.datetime.now().astimezone(local_tz)
        BlacklistedToken.objects.filter(Q(token__user__isnull=True) | Q(token__expires_at__lt=date_today)).delete()


class DeleteOutstandingTokens(CronJobBase):
    RUN_EVERY_MINS = 1
    RETRY_AFTER_FAILURE_MINS = 1
    schedule = Schedule(run_every_mins=RUN_EVERY_MINS, retry_after_failure_mins=RETRY_AFTER_FAILURE_MINS)
    code = "vanguard.delete_outstanding_tokens"

    def do(self):
        local_tz = get_localzone()
        date_today = datetime.datetime.now().astimezone(local_tz)
        OutstandingToken.objects.filter(Q(user__isnull=True) | Q(expires_at__lt=date_today)).delete()
