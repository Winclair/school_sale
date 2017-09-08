# -*- coding:utf-8 -*-
# __author__ = 'Shanks'

from flask import Blueprint

auth_buleprint = Blueprint('auth', __name__)

from . import views


