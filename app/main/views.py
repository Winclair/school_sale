# -*- coding:utf-8 -*-
# __author__ = 'Shanks'
# __date__: '2017-8-25'

from datetime import datetime
from flask import session, render_template, redirect, url_for
from . import main_blueprint
from .forms import Nameform
from .. import db
from ..models import User


@main_blueprint.route('/')
def index():
    return render_template('index.html')


@main_blueprint.route('/user/<name>')
def user(name):
    return render_template('user.html', name=name)





