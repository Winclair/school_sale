# -*- coding:utf-8 -*-
# __author__ = 'Shanks'

import csv
from flask_login import current_user
from flask_socketio import join_room

from app import socketio







@socketio.on_error()
def chat_error_handler(e):
    print('An error has occurred: ' + str(e))