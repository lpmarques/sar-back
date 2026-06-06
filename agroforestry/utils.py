# Simulador Agroflorestal Regenera (SAR)
# Copyright (C) 2026  Lucas Marques and Regenera Mata Atlântica

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses>.

from decimal import Decimal
import hashlib
import json
import numpy as np
from typing import Union
from core.models import User

def none_if_empty(value: str):
    value = value.strip()
    if len(value) == 0:
        return None

    return value

def none_if_nan(value):
    if np.issubdtype(type(value), np.number) and np.isnan(value):
        return None

    return value

def json_to_dict(json_str: Union[str, None]):
    if not json_str:
        return None

    return json.loads(json_str)

def hash_object(obj):
    def decimal_serializer(obj):
        if isinstance(obj, Decimal):
            return float(obj)
        raise TypeError(f"Type {type(obj)} not serializable")

    encoded = json.dumps(obj, sort_keys=True, default=decimal_serializer).encode()
    
    return hashlib.sha256(encoded).hexdigest()
