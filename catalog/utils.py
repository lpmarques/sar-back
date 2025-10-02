import hashlib

def string_to_md5(string):
    return hashlib.md5(string.encode('utf-8')).hexdigest()

def md5_to_color(md5):
    return "#" + md5[-6:]
