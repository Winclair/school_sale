# -*- coding:utf-8 -*-
# __author__ = 'Shanks'

from functools import wraps
from flask_login import current_user
from flask import abort
from .models import Permission


def permission_required(permission):
    def decorator(f):
        @wraps(f)
        def wrapped_func(*args, **kwargs):
            if not current_user.can(permission):
                abort(403)
            return f(*args, **kwargs)
        return wrapped_func
    return decorator


def admin_required(f):
    return permission_required(Permission.ADMINISTER)(f)


