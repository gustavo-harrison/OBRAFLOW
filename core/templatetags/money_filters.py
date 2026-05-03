from django import template

register = template.Library()


@register.filter
def clp(value):
    try:
        value = int(float(value))
        texto = f"{value:,}".replace(",", ".")
        return f"${texto}"
    except:
        return "$0"