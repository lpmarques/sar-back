import json
import numpy as np
from typing import Union

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
