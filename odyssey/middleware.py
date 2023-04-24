import random
import time

import django.core.exceptions
from django.conf import settings


class SleepMiddleware:
    def __init__(self, get_response):
        try:
            self.sleep_time = random.randint(settings.SLEEP_TIME_MIN, settings.SLEEP_TIME_MAX)
            self.get_response = get_response
        except AttributeError:
            raise django.core.exceptions.MiddlewareNotUsed
        if not isinstance(self.sleep_time, (int, float)) or self.sleep_time <= 0:
            raise django.core.exceptions.MiddlewareNotUsed

    def __call__(self, request):
        if "/odcwebapi/" in request.path:
            print(self.sleep_time)
            time.sleep(self.sleep_time)
        response = self.get_response(request)
        return response
