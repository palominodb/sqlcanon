from django import template

import canonicalizer.utils as app_utils

register = template.Library()

@register.filter
def hex_str(value):
    int_value = int(value)
    return app_utils.int_to_hex_str(int_value)
