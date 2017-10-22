# -*- coding:utf-8 -*-
# __author__ = 'Shanks'
# __date__: '2017-8-25'

import os
import csv
from time import time
from datetime import datetime
from threading import Lock

from flask import render_template, redirect, url_for, current_app, flash, request
from flask_login import login_required, current_user
from flask_socketio import join_room, emit

from app import socketio, redis_server
from . import main_blueprint
from .forms import SearchForm
from ..models import Goods, SchoolModel, id_results, Chat, User

thread = None
thread_lock = Lock()

# TODO:test


@main_blueprint.route('/', methods=["GET", "POST"])
def index():
    form = SearchForm()
    if form.validate_on_submit():
        sentence = form.search.data
        # 20 schools
        ids = id_results(sentence)[:20]
        sclmdls = []
        for i in ids:
            sclmdls.append(SchoolModel.query.get(i))
        return render_template('search.html', sclmdls=sclmdls)
    return render_template('index.html', form=form)


@main_blueprint.route('/<school>')
def schools(school):
    sholmdl = SchoolModel.query.filter_by(pinyin=school).first()
    if not sholmdl:
        return render_template('404.html')

    page = request.args.get('page', 1, type=int)
    pagination = Goods.query.filter_by(school=school).filter_by(faculty=-1).\
        order_by(Goods.time_stamp).paginate(
        page, per_page=current_app.config['GOODS_PER_PAGE'], error_out=False)
    goods = pagination.items

    return render_template('school.html', sholmdl=sholmdl, goods=goods, pagination=pagination)


@main_blueprint.route('/<school>-<int:faculty>')
def faculties(school, faculty):
    sholmdl = SchoolModel.query.filter_by(pinyin=school).first()
    if not sholmdl:
        return render_template('404.html')

    page = request.args.get('page', 1, type=int)
    pagination = Goods.query.filter_by(school=school).filter_by(faculty=faculty)\
        .order_by(Goods.time_stamp).paginate(
        page, per_page=current_app.config['GOODS_PER_PAGE'], error_out=False)
    goods = pagination.items

    return render_template('faculty.html', sholmdl=sholmdl, goods=goods,
                           pagination=pagination, faculty=faculty)


@main_blueprint.route('/<school>-<int:faculty>/sell', methods=["GET", "POST"])
@login_required
def sell(school, faculty):
    if request.method == 'POST':
        # save in database folder:
        image_dir = '{}/{}'.format(current_user.id, int(time()))
        os.makedirs('./app/static/imgs/{}'.format(image_dir))

        goods = Goods(seller=current_user._get_current_object(), title=request.form["title"],
                      kind=request.form["kind"], school=school, describe=request.form["describe"],
                      image_dir=image_dir, faculty=faculty)
        goods.save()

        for i in range(9):
            img = request.files['file{}'.format(i)]
            if img:
                path = './app/static/imgs/{}/{}.png'.format(image_dir, i)
                img.save(path)
        flash('Upload Successful')
        return redirect(url_for('main.faculties', school=school, faculty=faculty))
    return render_template('sell.html')


@main_blueprint.route('/details/<int:g_id>')
def details(g_id):
    goods = Goods.query.get_or_404(g_id)
    return render_template('details.html', goods=goods)


@main_blueprint.route('/delete')
@login_required
def delete():
    school = ''
    if request.method == 'GET':
        g_id = int(request.args['goods_id'])
        if g_id in [g.id for g in current_user.goods]:
            goods = Goods.query.get_or_404(g_id)
            school = goods.school
            goods.delete()
    return redirect(url_for('main.schools', school=school))


# TODO: chat-to-<int:seller_id> not work?
@main_blueprint.route('/chat_to_<int:seller_id>')
@login_required
def chat(seller_id):
    dir_id, file_id = min(seller_id, current_user.id), max(seller_id, current_user.id)
    path = './app/static/msgs/{}/{}.csv'.format(dir_id, file_id)
    dir_path = './app/static/msgs/{}'.format(dir_id)
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    messages = []
    if os.path.exists(path):
        with open(path, 'r') as csv_f:
            messages = list(csv.reader(csv_f))
    return render_template('chat.html', messages=messages, seller_id=seller_id)


@main_blueprint.route('/chatmsg')
@login_required
def chatmsg():
    chats = sorted(current_user.chats,key=lambda chat:chat.time_stamp, reverse=True)
    return render_template('chatmsg.html', chats=chats, User=User)


def get_room(sid, cid):
    min_id, max_id = min(sid, cid), max(sid, cid)
    return '{}-{}'.format(min_id, max_id)


def register_chat(user, to):
    chat = user.get_chat(to)
    if not user.chats or not chat:
        c = Chat(my=user, to=to)
        c.save()
    else:
        if user == current_user:
            chat.unread = 0
            chat.save()


@socketio.on('join', namespace='/chat')
def join():
    print('join')
    sid = int(request.headers['Referer'].split('_')[2])
    cid = current_user.id
    room = get_room(sid, cid)
    join_room(room)

    # put users in room, {id, numbers_of_unread_msg}
    room_id = '{}-id'.format(room)
    redis_server.hset(room_id, cid, 0)

    # register chat room
    register_chat(current_user, sid)
    seller = User.query.get(sid)
    register_chat(seller, cid)


@socketio.on('msg_to_server', namespace='/chat')
def message(data):
    msg = data.get('msg')
    print('server get message...', msg)
    cid = current_user.id
    sid = int(request.headers['Referer'].split('_')[2])
    room = get_room(sid, cid)
    if redis_server.lindex(room, 0):
        redis_server.rpushx(room, cid)
        redis_server.rpushx(room, msg)
    else:
        redis_server.rpush(room, cid, msg)
    
    # send massage to client
    room_id = '{}-id'.format(room)
    if sid in [int(i) for i in redis_server.hkeys(room_id)]:
        emit('to_client', {'msg': msg}, room=room, include_self=False)
    else:
        redis_server.hincrby(room_id, cid, 1)    


@socketio.on('connect', namespace='/chat')
def connect():
    print('server connect...')


def msg_to_file(room):
    ids = room.split('-')
    print('msg to file...')
    with open('./app/static/msgs/{}/{}.csv'.format(ids[0], ids[1]), 'a', newline='') as csv_f:
        writer = csv.writer(csv_f)
        i = 0
        while i < redis_server.llen(room):
            writer.writerow([str(redis_server.lindex(room, i), encoding='utf-8'),
                             str(redis_server.lindex(room, i + 1), encoding='utf-8')])
            i = i + 2
    redis_server.delete(room)


@socketio.on('disconnect', namespace='/chat')
def disconnect():
    print('server disconnect', request.sid)


@socketio.on_error(namespace='/chat')
def chat_error_handler(e):
    print('An error has occurred: ' + str(e))


# leave room and remember the number of unread massages
def out_room(room, sid, cid):
    # leave room
    room_id = '{}-id'.format(room)
    seller = User.query.get(sid)
    s_chat = seller.get_chat(cid)
    s_chat.unread += int(redis_server.hget(room_id, cid))
    s_chat.time_stamp = datetime.utcnow()
    s_chat.save()

    c_chat = current_user.get_chat(sid)
    c_chat.time_stamp = datetime.utcnow()
    c_chat.save()

    redis_server.hdel(room_id, cid)
    if len(redis_server.hkeys(room_id)) == 0:
        redis_server.delete(room_id)


@socketio.on('unload', namespace='/chat')
def unload():
    print('close')
    sid = int(request.headers['Referer'].split('_')[2])
    cid = current_user.id
    room = get_room(sid, cid)
    out_room(room, sid, cid)
    # save massage to file
    global thread
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(msg_to_file, room)

