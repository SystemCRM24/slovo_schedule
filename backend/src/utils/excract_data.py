from typing import Dict


def extract(obj) -> Dict:
    result = {}

    if isinstance(obj, type):
        attrs = dir(obj)
    elif isinstance(obj, dict):
        return obj
    else:
        return obj

    for key in attrs:
        if key.startswith('__'):
            continue
        value = getattr(obj, key)

        if isinstance(value, type):
            result[key] = extract(value)
        else:
            result[key] = value
    return result