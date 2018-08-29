from django import template

register = template.Library()


@register.filter(name='add_css')
def addcss(field, css):
    return field.as_widget(attrs={"class": css})
