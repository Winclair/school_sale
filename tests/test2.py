# -*- coding:utf-8 -*-
# __author__ = 'Shanks'
from flask import Flask, render_template
from flask_wtf import Form, validators
from wtforms import IntegerField, StringField, FormField



class TelephoneForm(Form):
    country_code = IntegerField('Country Code', [validators.required()])
    area_code = IntegerField('Area Code/Exchange', [validators.required()])
    number = StringField('Number')


class ContactForm(Form):
    first_name = StringField()
    last_name = StringField()
    mobile_phone = FormField(TelephoneForm)
    office_phone = FormField(TelephoneForm)

