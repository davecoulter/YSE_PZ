from django import template
from ..models import *

register = template.Library()

@register.filter
def has_group(user, group):
    return len(user.groups.filter(name='YSE'))
