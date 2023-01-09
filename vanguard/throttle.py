from rest_framework.throttling import UserRateThrottle, AnonRateThrottle


class OncePerMinuteAnonThrottle(AnonRateThrottle):
    rate = "1/minute"


class TwicePerMinuteAnonThrottle(AnonRateThrottle):
    rate = "2/minute"


class FivePerMinuteAnonThrottle(AnonRateThrottle):
    rate = "5/minute"


class TenPerMinuteAnonThrottle(AnonRateThrottle):
    rate = "10/minute"


class FifteenPerMinuteAnonThrottle(AnonRateThrottle):
    rate = "15/minute"
