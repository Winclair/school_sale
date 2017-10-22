# -*- coding:utf-8 -*-
# __author__ = 'Shanks'
# __date__: '2017-8-25'


from flask_wtf import FlaskForm, Form
from wtforms import StringField, SubmitField, IntegerField, FormField, SelectField, TextAreaField, \
    FileField
from wtforms.validators import DataRequired, Length


class Nameform(FlaskForm):
    name = StringField('What is your name?', validators=[DataRequired()])
    submit = SubmitField('Submit')


class SearchForm(FlaskForm):
    search = StringField(validators=[DataRequired(), Length(1, 20, message='最多字数为20字数')])
    submit = SubmitField('GO')


class FileForm(FlaskForm):
    file = FileField("upload file")
    submit = SubmitField("OK")


class SellForm(FlaskForm):
    kind = SelectField('king', validators=[DataRequired()], choices=[('b', 'BOOK'), ('o', 'OTHER')])
    describe = TextAreaField('describe your goods', validators=[DataRequired("please describe your goods")])
    submit = SubmitField('DONE')



