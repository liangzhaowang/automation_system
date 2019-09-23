from django import template

register = template.Library()

@register.simple_tag()
def chart_view(attachment):
    if '_'.join(attachment.split('_')[:-1]) == 'report':
        return True
    else:
        return ''