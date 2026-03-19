# Simulador Agroflorestal Regenera (SAR)
# Copyright (C) 2026  Lucas Marques and Regenera Mata Atlântica

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses>.

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
