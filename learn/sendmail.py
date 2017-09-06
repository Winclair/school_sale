# -*- coding:utf-8 -*-
# __author__ = 'Shanks'
import os
from flask import Flask
from flask_mail import Mail, Message

app = Flask(__name__)
# Q:https://stackoverflow.com/questions/37058567/configure-flask-mail-to-use-gmail
app.config.update(
    DEBUG=True,
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=465,
    MAIL_USE_SSL=True,
    MAIL_USERNAME='1996sinclair@gmail.com',
    MAIL_PASSWORD=os.getenv('MAIL_PASSWORD'),
    MAIL_DEBUG=True

)

mail = Mail(app)


def send_mail():
    msg = Message('hello', sender='1996sinclair@gmail.com', recipients=['3228367978@qq.com'])
    msg.body = 'this is my first mail!'
    mail.send(msg)


if __name__ == '__main__':
    with app.app_context():
        send_mail()
