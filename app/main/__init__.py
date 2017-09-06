# -*- coding:utf-8 -*-
# __author__ = 'Shanks'
# __date__: '2017-8-25'

from flask import Blueprint

main_blueprint = Blueprint('main', __name__, template_folder='templates')

from . import errors, views




