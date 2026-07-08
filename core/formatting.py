from decimal import Decimal

def safe_float(value):
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    try:
        return float(value)
    except Exception:
        return None

def format_tl(value):
    value = safe_float(value)
    if value is None:
        return "-"
    return f"{value:,.2f} TL".replace(",", "X").replace(".", ",").replace("X", ".")

def format_number(value):
    value = safe_float(value)
    if value is None:
        return "-"
    return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def format_percent(value):
    value = safe_float(value)
    if value is None:
        return "-"
    return f"%{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def format_date(value):
    if value is None:
        return "-"
    try:
        return value.strftime("%d.%m.%Y")
    except Exception:
        return str(value)
