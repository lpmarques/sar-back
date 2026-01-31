def none_if_empty(value: str):
    value = value.strip()
    if len(value) == 0:
        return None

    return value
