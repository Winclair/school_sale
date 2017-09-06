# -*- coding:utf-8 -*-
# __author__ = 'Shanks'

from . import mail
from flask_mail import Message
from flask import render_template, current_app
from threading import Thread


def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)


def send_mail(subject, to, template, **kwargs):
    app = current_app._get_current_object()
    msg = Message(app.config['FLASKY_MAIL_SUBJECT_PREFIX'] + subject, to,
                  sender=app.config['FLASKY_MAIL_SENDER'])
    msg.body = render_template(template + '.txt',  **kwargs)
    msg.html = render_template(template + '.html', **kwargs)
    # moving the progress of sending email to background thread
    thr = Thread(target=send_async_email, args=[app, msg])
    thr.start()
    return thr


