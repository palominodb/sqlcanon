"""Utility functions."""

def int_to_hex_str(n):
    """Returns hex representation of a number."""

    return '%08X' % (n & 0xFFFFFFFF,)