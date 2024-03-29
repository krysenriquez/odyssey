import os
from pathlib import Path
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "django-insecure-2tj+!nv*4b7yy!i+#%m24cqv=4+nzwsaxh-dcw&k31po9exolv"

DEBUG = False
LIVE = True

if DEBUG and not LIVE:
    ALLOWED_HOSTS = ["*"]

if LIVE:
    ALLOWED_HOSTS = [
        "https://member.topchoiceinternational.com",
        "https://admin.topchoiceinternational.com",
        "https://odyssey.topchoiceinternational.com",
        "member.topchoiceinternational.com",
        "admin.topchoiceinternational.com",
        "odyssey.topchoiceinternational.com",
        "https://139.59.251.241",
    ]

CORS_ORIGIN_ALLOW_ALL = False
CORS_ALLOW_CREDENTIALS = True

if LIVE:
    CORS_ALLOWED_ORIGINS = [
        "https://member.topchoiceinternational.com",
        "https://admin.topchoiceinternational.com",
        "https://odyssey.topchoiceinternational.com",
        "https://139.59.251.241",
    ]
    CSRF_TRUSTED_ORIGINS = [
        "https://member.topchoiceinternational.com",
        "https://admin.topchoiceinternational.com",
        "https://odyssey.topchoiceinternational.com",
        "https://139.59.251.241",
    ]
else:
    CORS_ALLOWED_ORIGINS = [
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "http://localhost:3002",
        "http://127.0.0.1:3002",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]
    CSRF_TRUSTED_ORIGINS = [
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "http://localhost:3002",
        "http://127.0.0.1:3002",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "django_cron",
    "corsheaders",
    "rest_framework_simplejwt.token_blacklist",
    "users",
    "accounts",
    "core",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "odyssey.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [Path.absolute(Path(BASE_DIR, "statics", "templates"))],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_AUTHENTICATION_CLASSES": ("rest_framework_simplejwt.authentication.JWTAuthentication",),
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {"anon": "20/minute", "user": "10000/day"},
    "DATE_INPUT_FORMATS": ["iso-8601", "%Y-%m-%dT%H:%M:%S.%fZ"],
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=50),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=90),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": False,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "VERIFYING_KEY": None,
    "AUDIENCE": None,
    "ISSUER": None,
    "JWK_URL": None,
    "LEEWAY": 0,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "USER_AUTHENTICATION_RULE": "rest_framework_simplejwt.authentication.default_user_authentication_rule",
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "TOKEN_TYPE_CLAIM": "token_type",
    "TOKEN_USER_CLASS": "rest_framework_simplejwt.models.TokenUser",
    "JTI_CLAIM": "jti",
    "SLIDING_TOKEN_REFRESH_EXP_CLAIM": "refresh_exp",
    "SLIDING_TOKEN_LIFETIME": timedelta(minutes=5),
    "SLIDING_TOKEN_REFRESH_LIFETIME": timedelta(days=1),
}

WSGI_APPLICATION = "odyssey.wsgi.application"

# Logger
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "filters": {
        "require_debug_true": {
            "()": "django.utils.log.RequireDebugTrue",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "filters": ["require_debug_true"],
        },
    },
    "loggers": {
        "odysseyLogger": {
            "handlers": ["console"],
            "level": os.getenv("DJANGO_LOG_LEVEL", "INFO"),
            "propagate": True,
        },
    },
}

if LIVE:
    if DEBUG:
        DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.postgresql_psycopg2",
                "NAME": "odysseydb_uat",
                "USER": "odyssey",
                "PASSWORD": "ody$$3y",
                "HOST": "localhost",
                "PORT": "5432",
            }
        }
    else:
        DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": "odysseydb",
                "USER": "odyssey",
                "PASSWORD": "ody$$3y",
                "HOST": "localhost",
                "PORT": "5432",
            }
        }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql_psycopg2",
            "NAME": "odysseydb",
            "USER": "postgres",
            "PASSWORD": "Pass1word",
            "HOST": "localhost",
            "PORT": "5432",
        }
    }


# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

AUTH_USER_MODEL = "users.User"

AUTHENTICATION_BACKENDS = (
    "django.contrib.auth.backends.ModelBackend",
    "vanguard.backends.UserAuth",
)


LANGUAGE_CODE = "en-us"

TIME_ZONE = "Asia/Manila"

USE_I18N = True

USE_TZ = True


STATIC_URL = "/statics/"

STATICFILES_DIRS = [
    Path(BASE_DIR, "statics"),
]

if not DEBUG:
    STATIC_ROOT = Path(BASE_DIR, "static_cdn")

STATIC_ROOT = Path(BASE_DIR, "static_cdn")

MEDIA_ROOT = Path.absolute(Path(BASE_DIR, "statics", "media"))
MEDIA_URL = "/media/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


CRON_CLASSES = [
    "vanguard.cron.DeleteBlacklistedTokens",
    "vanguard.cron.DeleteOutstandingTokens",
]


EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtpout.asia.secureserver.net"
EMAIL_HOST_USER = "tcisupport@topchoiceinternational.com"
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
EMAIL_HOST_PASSWORD = "TopChoice2022!"
EMAIL_PORT = 80
EMAIL_USE_SSL = False
EMAIL_USE_TLS = True
