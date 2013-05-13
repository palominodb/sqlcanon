"""Sqlcanon template tags."""

from django import template

from sqlcanon import utils

register = template.Library()


@register.filter
def hex_str(value):
    """Template filter for displaying hex string equivalent of value."""

    int_value = int(value)
    return utils.int_to_hex_str(int_value)
