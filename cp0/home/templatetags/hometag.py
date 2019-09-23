from django import template
import os

register = template.Library()


@register.simple_tag()
def active(url, current):
    if len(current.split('/')) >= 2:
        current = current.split('/')[1]
        if current == url:
            return 'active'


@register.simple_tag()
def active_sub(url, current):
    if len(current.split('/')) >= 3:
        current = current.split('/')[2]
        if current == url:
            return 'active'


@register.filter
def filesize(num, suffix='B'):
    for unit in ['', 'K', 'M', 'G', 'T', 'P']:
        if abs(num) < 1024.0:
            return "%3.1f %s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f %s%s" % (num, 'Y', suffix)
