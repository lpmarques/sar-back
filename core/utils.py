from core.models import User

def full_name(user: User):
    return f"{user.first_name} {user.last_name}"
