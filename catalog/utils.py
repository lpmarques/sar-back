import hashlib

def string_to_md5(string):
    return hashlib.md5(string.encode('utf-8')).hexdigest()

def md5_to_color(md5):
    return "#" + md5[-6:]

def none_if_empty(value: str):
    value = value.strip()
    if len(value) == 0:
        return None

    return value
