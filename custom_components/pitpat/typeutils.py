from datetime import datetime

import dateutil


def to_nullable_int(value: str) -> int | None:
    '''Returns the value as a int, or None if the value is None or empty.'''
    if value is None or value == '':
        return None
    return int(value)

def to_nullable_float(value: str) -> float | None:
    '''Returns the value as a float, or None if the value is None or empty.'''
    if value is None or value == '':
        return None
    return float(value)

def to_nullable_datetime(value: str) -> datetime | None:
    '''Returns the value as an int, or None if the value is None or empty.'''
    if value is None or value == '':
        return None
    return dateutil.parser.parse(value)
