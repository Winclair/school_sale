# -*- coding:utf-8 -*-
# __author__ = 'Shanks'

from flask import Flask
from flask_mail import Mail, Message

app = Flask(__name__)
mail = Mail(app)

mess = Message('hello', recipients='3228367978@qq.com', sender='3228367978@qq.com')
mail.send(mess)
