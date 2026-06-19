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
        
    def extrair_comparavel(num: str) -> str:
        # Remove DDI 55 se houver
        if num.startswith("55"):
            num = num[2:]
        # Se for celular com DDD + 9 + 8 dígitos (11 dígitos, terceiro é 9)
        if len(num) == 11 and num[2] == "9":
            # Remove o '9' do celular para virar DDD + 8 dígitos (10 dígitos)
            return num[:2] + num[3:]
        return num

    return extrair_comparavel(a) == extrair_comparavel(b)
