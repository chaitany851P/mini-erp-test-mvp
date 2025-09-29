from django import template

register = template.Library()

@register.filter(name='has_group')
def has_group(user, group_name: str):
    try:
        return user.is_authenticated and (user.is_superuser or user.groups.filter(name=group_name).exists())
    except Exception:
        return False
