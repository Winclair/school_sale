# -*- coding:utf-8 -*-
# __author__ = 'Shanks'
import os

from flask import abort, render_template, flash, request, url_for, current_app
from flask_login import login_required, current_user
from werkzeug.utils import redirect

from .forms import EditProfileForm
from . import user_blueprint
from ..models import User


@user_blueprint.route('/user/<username>')
def user(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        abort(404)
    return render_template('user/user.html', user=user)


@user_blueprint.route('/user/edit-profile', methods=["GET", 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if request.method == 'POST':
        if form.user_image.data:
            path = './app/static/imgs/{}/header.png'.format(current_user.id)
            form.user_image.data.save(path)
        current_user.nickname = form.nickname.data
        current_user.school = form.school.data
        current_user.campus = form.campus.data
        current_user.faculty = form.faculty.data
        current_user.gender = form.gender.data
        current_user.about_me = form.about_me.data
        current_user.save()
        flash('Edit Successful')
        return redirect(url_for('user.user', username=current_user.username))

    form.nickname.data = current_user.nickname
    form.school.data = current_user.school
    form.campus.data = current_user.campus
    form.faculty.data = current_user.faculty
    form.gender.data = current_user.gender
    form.about_me.data = current_user.about_me
    return render_template('user/edit_profile.html', form=form)
