# -*- coding:utf-8 -*-
# __author__ = 'Shanks'
import threading

import jieba
import multiprocessing
import xlrd
import os
import shutil
from time import time
from datetime import datetime
from flask import current_app
from itsdangerous import TimedJSONWebSignatureSerializer as TJSerializer
from flask_login import UserMixin, AnonymousUserMixin
from pypinyin import lazy_pinyin, Style
from werkzeug.security import generate_password_hash, check_password_hash
from . import db, login_manager


class Permission:
    FOLLOW = 0b00000001
    COMMENT = 0b00000010
    WRITE_ARTICLES = 0b00000100
    MANAGE_COMMENT = 0b00001000
    ADMINISTER = 0b10000000


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    # relation
    users = db.relationship('User', backref='role')
    # only user's default is True, other is false
    default = db.Column(db.Boolean, default=False, index=True)

    # the value of permissions
    # For instants, User has the permissions of follow, comment, write articles
    # so it's the value of permissions is 0b00000111
    # other like that
    permissions = db.Column(db.Integer)

    @staticmethod
    def insert_roles():
        roles = {'User': (0b00000111, True),
                 'Moderator': (0b00001111, True),
                 'Administer': (0b11111111, True)
                 }
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
                role.permissions = roles[r][0]
                role.default = roles[r][1]
                db.session.add(role)
        db.session.commit()

    def __repr__(self):
        return '<Role {}>'.format(self.name)


class Goods(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    kind = db.Column(db.String(32), index=True)
    title = db.Column(db.String(64))
    describe = db.Column(db.Text())
    image_dir = db.Column(db.String(64))
    school = db.Column(db.String(32), index=True)
    faculty = db.Column(db.Integer, index=True)
    time_stamp = db.Column(db.DateTime, default=datetime.utcnow())
    seller_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    def img_urls(self):
        url_dir = '/static/imgs/{}'.format(self.image_dir)
        absdir = './app/static/imgs/{}'.format(self.image_dir)
        if os.path.exists(absdir):
            fnames = os.listdir(absdir)
            return [url_dir + '/{}'.format(fname) for fname in fnames]
        else:
            return ['/static/imgs/anony.png']

    def date_stamp(self):
        return self.time_stamp.strftime('%Y-%m-%d')

    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        shutil.rmtree(r'./app/static/imgs/{}'.format(self.image_dir))
        db.session.delete(self)
        db.session.commit()        


class User(UserMixin, db.Model):
    """ generally, User include other roles except anonymous, so other roles can be defined in this class.
    increase role attibute

"""
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    goods = db.relationship('Goods', backref='seller', lazy='dynamic')
    password_hash = db.Column(db.String(128))
    email = db.Column(db.String(64), unique=True, index=True)
    # TODO: add confirm action, but at the same time, we need to prevent server tracked by other.
    is_confirmed = db.Column(db.Boolean())

    # user profile
    # TODO: String(64), 64 bit or 64 words?
    image_url = db.Column(db.String(64))
    nickname = db.Column(db.String(64))
    school = db.Column(db.String(64))
    campus = db.Column(db.String(64))
    faculty = db.Column(db.String(64))
    gender = db.Column(db.String(8))
    about_me = db.Column(db.Text())

    # about chat
    chats = db.relationship('Chat', backref='my', lazy='dynamic')


    def __init__(self, **kwargs):
        # TODO: what is mean?
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.email == current_app.config['FLASKY_ADMIN']:
                self.role = Role.query.filter_by(permissions=0b11111111).first()
            else:
                self.role = Role.query.filter_by(default=True).first()

            self.role_id = self.role.id

    def img_url(self):
        if os.path.exists('./app/static/imgs/{}/header.png'.format(self.id)):
            return '/static/imgs/{}/header.png'.format(self.id)
        else:
            return '/static/imgs/header.png'

    # permission
    def can(self, permission):
        return self.role is not None and \
               (self.role.permissions & permission) == permission

    def is_administer(self):
        return self.can(Permission.ADMINISTER)

    def save(self):
        db.session.add(self)
        db.session.commit()

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

    def all_unread(self):
        count = 0
        for chat in self.chats:
            count += chat.unread
        return count

    def get_chat(self, to):
        for c in self.chats:
            if c.to == to:
                return c


    def __repr__(self):
        return '<User %r>' % self.username


class AnonymousUser(AnonymousUserMixin):
    def can(self, permission):
        return False

    def is_administer(self):
        return False

    def img_url(self):
        return '/static/imgs/header.png'

    def all_unread(self):
        return 0


# chat room
class Chat(db.Model):
    __tablename__ = 'chats'
    id = db.Column(db.Integer, primary_key=True)
    to = db.Column(db.Integer)
    unread = db.Column(db.Integer, default=0)
    time_stamp = db.Column(db.DateTime)
    my_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    def save(self):
        db.session.add(self)
        db.session.commit()


class SchoolModel(db.Model):
    REGULAR = 0
    JUNIOR = 1

    __tablename__ = 'schools'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, index=True)
    pinyin = db.Column(db.String(64), unique=True)
    faculties = db.Column(db.PickleType)
    # lever 0 is regular college, lever 1 is junior college
    lever = db.Column(db.Integer)

    def save(self):
        db.session.add(self)
        db.session.commit()

    def faculty_name(self, faculty):
        for key in self.faculties.keys():
            if self.faculties[key] == faculty:
                return key

def topy(hans):
    return ''.join(lazy_pinyin(hans, style=Style.FIRST_LETTER))


def register():
    f = xlrd.open_workbook(r'D:\WORD\dxmd.xls')
    table = f.sheet_by_index(0)

    for i in range(table.nrows):
        if type(table.cell(i, 0).value) == float:
            name = table.cell(i, 1).value
            lever = 0 if table.cell(i, 4).value == '本科' else 1
            school = SchoolModel(name=name, pinyin=topy(name), lever=lever)
            school.save()


def search(word):
    id_list = []
    for s in SchoolModel.query.all():
        if word in s.name:
            id_list.append(s.id)
    return id_list


def id_results(sentence):
    words = jieba.cut(sentence)
    result = []
    for w in words:
        result += search(w)
    reset = set(result)
    return sorted(reset, key=lambda i: result.count(i), reverse=True)


def get_faculty():
    print('begin...')
    with open(r'C:\Users\Administrator\Desktop\faculties2.txt', 'r') as f:
        last = f.readline().strip()
        while 1:
            if not last:
                break
            cut = last.split('-')
            school = SchoolModel.query.filter_by(name=cut[0]).first()
            if not school:
                print(cut[0])
                last = f.readline().strip()
                continue
            i = 0
            school.faculties = {}
            school.faculties[cut[1]] = i

            while 1:
                line1 = f.readline().strip()
                cut1 = line1.split('-')
                if not line1 or cut1[0] != cut[0]:
                    last = line1
                    school.save()
                    break
                i = i + 1
                school.faculties[cut1[1]] = i



login_manager.anonymous_user = AnonymousUser

# TODO: how to use???
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

