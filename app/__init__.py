# -*- coding:utf-8 -*-
# __author__ = 'Shanks'
# __date__: '2017-8-24'

from flask import Flask
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
from config import config
# WRONG: from .main import main_blueprint
# WRONG: because current this model not include db!

# global variable in package app
bootstrap = Bootstrap()
mail = Mail()
moment = Moment()
db = SQLAlchemy()


def create_app(config_name):

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    config[config_name].init_app(app)
    bootstrap.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    db.init_app(app)

    # add error and route
    # !!! don't put it in the wrong place
    from .main import main_blueprint
    app.register_blueprint(main_blueprint)

    return app


