from users.models import User

def create_new_user(request):
    data = {
        "username": request["username"],
        "email_address": request["email_address"],
    }
    user = User.objects.create(**data)
    user.set_password(request["password"])
    user.save()
    return user
