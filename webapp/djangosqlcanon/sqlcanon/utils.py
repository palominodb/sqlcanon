"""Utility functions."""

def int_to_hex_str(n):
    """Returns hex representation of a number."""

    return '%08X' % (n & 0xFFFFFFFF,)


def generate_model_instance_unicode_string(instance):
    """Generates a unicode string as representation of a model instance."""

    parts = []
    for k, v in vars(instance).iteritems():
        if not k.startswith('_'):
            parts.append(u'%s=%s' % (k, v))
    return u', '.join(parts)
