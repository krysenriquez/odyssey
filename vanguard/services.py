from django.conf import settings
from django.core.signing import Signer, BadSignature
from django.core.mail import EmailMessage
import datetime
from tzlocal import get_localzone


def send_email(subject, body, email):
    try:
        email_msg = EmailMessage(subject, body, settings.EMAIL_HOST_USER, [email], reply_to=[email])
        email_msg.content_subtype = "html"
        email_msg.send()
        return "Email Sent"
    except:
        return "Email failed, try again later."


def create_reset_password_link(request, user):
    signer = Signer()
    local_tz = get_localzone()
    expiration = datetime.datetime.now().astimezone(local_tz) + datetime.timedelta(minutes=5)
    data = {"user": user.pk, "email_address": user.email_address, "expiration": expiration.isoformat()}

    signed_obj = signer.sign_object(data)
    url = request.build_absolute_uri("https://admin.topchoiceinternational.com/reset-password?data=" + signed_obj)
    return url


def verify_reset_password_link(data):
    signer = Signer()
    try:
        unsigned_obj = signer.unsign_object(data)
        local_tz = get_localzone()
        is_expired = datetime.datetime.now().astimezone(local_tz) > datetime.datetime.fromisoformat(
            unsigned_obj["expiration"]
        )
        if not is_expired:
            return True, unsigned_obj

        return False, "Link Expired"
    except BadSignature:
        return False, "Invalid Link"
