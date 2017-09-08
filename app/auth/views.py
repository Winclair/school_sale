# -*- coding:utf-8 -*-
# __author__ = 'Shanks'

from flask_login import login_user, login_required, logout_user, current_user
from flask import render_template, redirect, url_for, request, abort, flash
from . import auth_buleprint
from .forms import LoginForm, RegistrationForm, ChangeEmailForm, ChangePasswordForm,\
    ResetPasswordRequestForm, ResetPasswordForm
from ..models import User
from .. import db
from ..email import send_mail


@auth_buleprint.route('/unconfirmed')
@login_required
def unconfirmed():
    return render_template('auth/unconfirmed.html')


@auth_buleprint.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            flash('You has been logged in.')
            # check if the user has confirmed
            if user.is_authenticated and not user.is_confirmed:
                return redirect(url_for('auth.unconfirmed'))
            # TODO: valid next_url to prevent tracked by other
            next_url = request.args.get('next')
            return redirect(next_url or url_for('main.index'))

    return render_template('auth/login.html', form=form)


@auth_buleprint.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('main.index'))


@auth_buleprint.route('/register', methods=['GET', 'POST'])
def register():

    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data,
                    email=form.email.data,
                    password=form.password.data)
        db.session.add(user)
        db.session.commit()
        token = user.generate_confirmation_token()
        send_mail('Confirm your Account', 'auth/email/confirm',
                  [form.email.data], user=user, token=token)
        flash('A confirmation email has been sent to your email...')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', form=form)


@auth_buleprint.route('/confirm')
@login_required
def resend_confirmation():
    token = current_user.generate_confirmation_token()
    send_mail('Confirm your Account', 'auth/email/confirm',
              [current_user.email], user=current_user, token=token)
    flash('A new confirmation email has been sent to your email...')
    return redirect(url_for('main.index'))


@auth_buleprint.route('/confirm/<token>')
@login_required
def confirm(token):
    if current_user.confirmed(token):
        flash('Your have confirmed your account. Thanks!')
    else:
        flash('The confirmation link is invalid or has expired')
    return redirect(url_for('main.index'))


@auth_buleprint.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.old_password.data):
            current_user.password = form.new_password.data
            db.session.add(current_user)
            db.session.commit()
            flash('Your password has been updated')
            return redirect(url_for('main.index'))
        else:
            flash('Invalid Password')
    return render_template('auth/change_password.html', form=form)


@auth_buleprint.route('/change_email', methods=['GET', 'POST'])
@login_required
def change_email_request():
    form = ChangeEmailForm()
    if form.validate_on_submit():
        new_email = form.new_email.data
        print('#####################')
        print(form.password)
        if current_user.verify_password(form.password.data):
            token = current_user.generate_new_email_token(new_email)
            send_mail('Validate your new email', 'auth/email/change_email', [new_email],
                      user=current_user, token=token)
            flash('A new email sending to you for validating your new email...')
            return redirect(url_for('main.index'))
        else:
            flash('Invalid Password')

    return render_template('auth/change_email.html', form=form)


@auth_buleprint.route('/change_email/<token>')
@login_required
def change_email(token):
    if current_user.email_changed(token):
        flash('Your has changed your email!')
    else:
        flash('Invalid Request')
    return redirect(url_for('main.index'))


@auth_buleprint.route('/reset_password', methods=['GET', 'POST'])
@login_required
def reset_password_request():
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            token = user.generate_reset_password_token()
            send_mail('Reset your password', 'auth/email/reset_password',
                      [form.email.data], user=user, token=token)
            flash('An email with instructions to reset your password has been '
                  'sent to you.')
        else:
            flash('Invalid Email, returning login frame...')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password.html', form=form)


@auth_buleprint.route('/reset_password/<token>', methods=['GET', 'POST'])
@login_required
def reset_password(token):
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            if user.password_reset(token, form.password.data):
                flash('Your password has been updated.')
                return redirect(url_for('auth.login'))
        else:
            flash('Invalid Email.')
    return render_template('auth/reset_password.html', form=form)

