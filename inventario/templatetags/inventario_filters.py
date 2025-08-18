# inventario/templatetags/inventario_filters.py
from django import template

register = template.Library()

@register.filter
def subtract(value, arg):
    """Subtracts the arg from the value."""
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return '' # Or handle error as appropriate

@register.filter(name='verbose_name')
def get_verbose_name(field):
    """
    Retorna el verbose_name de un campo del formulario.
    """
    return field.field.label

@register.filter
def get_item(dictionary, key):
    """
    Permite acceder a un valor de diccionario usando una clave
    en las plantillas de Django.
    Ejemplo: {{ my_dict|get_item:my_key }}
    """
    return dictionary.get(key)