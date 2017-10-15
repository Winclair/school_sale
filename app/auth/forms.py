# -*- coding:utf-8 -*-
# __author__ = 'Shanks'

from flask_wtf import Form, FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, IntegerField, FormField, \
    SelectField, FieldList
from wtforms.validators import DataRequired, Email, Length, Regexp, EqualTo
from wtforms import ValidationError
from ..models import User


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Keep me logged in')
    submit = SubmitField('log in')


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(1, 64),
                                                   Regexp('[A-Za-z]\w*$',
                                                          message='username must have only letters,'
                                                          'numbers, dot or underscores')])
    email = StringField('Email', validators=[DataRequired(), Email()])
    school = SelectField('school', choices=[('华南师范大学大学城校区', 'scnu'), ('中山大学东校区', 'scyu')])
    password = PasswordField('password', validators=[DataRequired(),
                                                     EqualTo('password2', 'password must match!')])
    password2 = PasswordField('Confirm password', validators=[DataRequired()])
    submit = SubmitField('Register')

    # auth validate
    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already registered')


class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('Old password', validators=[DataRequired()])
    new_password = PasswordField('New password', validators=[DataRequired(),
                                                             EqualTo('new_password2',
                                                                     'Password must match')])
    new_password2 = PasswordField('Confirm your password')
    submit = SubmitField('Update Password')


class ChangeEmailForm(FlaskForm):
    new_email = StringField('New Email', validators=[DataRequired(), Email()])
    password = PasswordField('password', validators=[DataRequired()])
    submit = SubmitField('Update Email Address')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered')


class ResetPasswordRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Reset Password')


class ResetPasswordForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('password', validators=[DataRequired(),
                                                     EqualTo('password2', 'password must match!')])
    password2 = PasswordField('Confirm password', validators=[DataRequired()])
    submit = SubmitField('Reset')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first() is None:
            raise ValidationError('Unknown email address.')




















