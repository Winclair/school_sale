# -*- coding:utf-8 -*-
# __author__ = 'Shanks'

from flask import Blueprint

user_blueprint = Blueprint('user', __name__)

from . import views

