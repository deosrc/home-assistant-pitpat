from datetime import datetime

import dateutil


def to_nullable_datetime(value: str) -> datetime | None:
    '''Returns the value as an int, or None if the value is None or empty.'''
    if value is None or value == '':
        return None
    return dateutil.parser.parse(value)
