# -*- coding:utf-8 -*-
# __author__ = 'Shanks'
# __date__: '2017-8-25'

from flask import Blueprint
from ..models import Permission

main_blueprint = Blueprint('main', __name__, template_folder='templates')

# making Permission class to be globally accessible in all templates
@main_blueprint.app_context_processor
def insert_permission():
    return dict(Permission=Permission)

from . import errors, views




