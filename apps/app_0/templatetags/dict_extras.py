from django import template

register = template.Library()

@register.filter(name='get_item')
def get_item(mapping, key):
    try:
        return mapping.get(key)
    except Exception:
        return ''


@register.filter(name='split')
def split(value, sep=','):
    try:
        return value.split(sep)
    except Exception:
        return [value]
