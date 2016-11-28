from functools import wraps

import botocore.exceptions

from click import ClickException


EXC_TO_ECHO = [
    botocore.exceptions.NoRegionError,
]


def handle_exception(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as exc:
            if exc.__class__ in EXC_TO_ECHO:
                msg = '%s: %s' % (exc.__class__, exc)
                raise ClickException(msg)
            raise
    return wrapper
