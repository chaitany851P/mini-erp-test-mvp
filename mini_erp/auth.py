from functools import wraps
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden


def user_in_groups(user, groups):
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    user_groups = set(user.groups.values_list('name', flat=True))
    return any(group in user_groups for group in groups)


def role_required(roles):
    """Decorator enforcing that the user belongs to any of the given roles (Django groups)."""
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped(request, *args, **kwargs):
            if user_in_groups(request.user, roles):
                return view_func(request, *args, **kwargs)
            return HttpResponseForbidden("You do not have permission to perform this action.")
        return _wrapped
    return decorator
