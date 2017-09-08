# -*- coding:utf-8 -*-
# __author__ = 'Shanks'

from flask import current_app
from itsdangerous import TimedJSONWebSignatureSerializer as TJSerializer
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from . import db, login_manager


# database
class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)

    # relation
    users = db.relationship('User', backref='role')

    def __repr__(self):
        return '<Role {}>'.format(self.name)


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    password_hash = db.Column(db.String(128))
    email = db.Column(db.String(64), unique=True, index=True)
    # TODO: add confirm action, but at the same time, we need to prevent server tracked by other.
    is_confirmed = db.Column(db.Boolean())


    @property
    def password(self):
        raise AttributeError('password is not a readable attribution')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_confirmation_token(self, expiration=1800):
        s = TJSerializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id})

    def confirmed(self, token):
        if self.is_confirmed:
            return True
        s = TJSerializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.is_confirmed = True
        db.session.add(self)
        db.session.commit()
        return True

    def generate_new_email_token(self, new_email, expiration=1800):
        s = TJSerializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'user_id': self.id, 'new_email': new_email})

    def email_changed(self, token):
        s = TJSerializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if self.id != data.get('user_id'):
            return False
        self.email = data.get('new_email')
        db.session.add(self)
        db.session.commit()
        return True

    def generate_reset_password_token(self, expiration=1800):
        s = TJSerializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'reset': self.id})

    def password_reset(self, token, new_password):
        s = TJSerializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if self.id != data.get('reset'):
            return False
        self.password = new_password
        db.session.add(self)
        db.session.commit()
        return True


    def __repr__(self):
        return '<User %r>' % self.username


# TODO: how to use???
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
