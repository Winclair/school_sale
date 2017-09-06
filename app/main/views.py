# -*- coding:utf-8 -*-
# __author__ = 'Shanks'
# __date__: '2017-8-25'

from datetime import datetime
from flask import session, render_template, redirect, url_for
from . import main_blueprint
from .forms import Nameform
from .. import db
from ..models import User


@main_blueprint.route('/', methods=['GET', 'POST'])
def index():
    form = Nameform()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.name.data).first()
        if user is None:
            user = User(username=form.name.data)
            db.session.add(user)
            db.session.commit()
            session['known'] = False
        else:
            session['known'] = True
        session['name'] = form.name.data
        form.name.data = ''
        return redirect(url_for('.index'))
    return render_template('index.html', name=session.get('name'), form=form,
                           known=session.get('known', False),
                           current_time=datetime.utcnow())


@main_blueprint.route('/user/<name>')
def user(name):
    return render_template('user.html', name=name)





