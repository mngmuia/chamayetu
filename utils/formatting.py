def money(value, currency="KES"):
    try:
        return f"{currency} {float(value or 0):,.2f}"
    except Exception:
        return f"{currency} 0.00"
