def normalize_phone(phone: str) -> str:
    digits = "".join(c for c in phone if c.isdigit())
    if len(digits) == 11:
        return f"55{digits}"
    if len(digits) == 10:
        return f"55{digits}"
    return digits


def phones_match(stored: str, incoming: str) -> bool:
    a = normalize_phone(stored)
    b = normalize_phone(incoming)
    if a == b:
        return True
    if len(a) >= 11 and len(b) >= 11 and a[-11:] == b[-11:]:
        return True
    return False
