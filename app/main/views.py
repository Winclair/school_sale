# -*- coding:utf-8 -*-
# __author__ = 'Shanks'
# __date__: '2017-8-25'

import os
import csv
from time import time
from threading import Lock

from flask import render_template, redirect, url_for, current_app, flash, request
from flask_login import login_required, current_user
from flask_socketio import join_room, emit

from app import socketio, redis_server
from . import main_blueprint
from .forms import SearchForm
from ..models import Goods, SchoolModel, id_results

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
    if not SchoolModel.query.filter_by(pinyin=school).first():
        return render_template('404.html')

    page = request.args.get('page', 1, type=int)
    pagination = Goods.query.filter_by(school=school).order_by(Goods.time_stamp).paginate(
        page, per_page=current_app.config['GOODS_PER_PAGE'], error_out=False)
    goods = pagination.items

    return render_template('school.html', school=school, goods=goods, pagination=pagination)


@main_blueprint.route('/<school>/sell', methods=["GET", "POST"])
@login_required
def sell(school):
    if request.method == 'POST':
        # save in database folder:
        image_dir = '{}/{}'.format(current_user.id, int(time()))
        os.makedirs('./app/static/imgs/{}'.format(image_dir))

        goods = Goods(seller=current_user._get_current_object(), title=request.form["title"],
                      kind=request.form["kind"], school=school, describe=request.form["describe"],
                      image_dir=image_dir)
        goods.save()

        for i in range(9):
            img = request.files['file{}'.format(i)]
            if img:
                path = './app/static/imgs/{}/{}.png'.format(image_dir, i)
                img.save(path)
        flash('Upload Successful')
        return redirect(url_for('main.schools', school=school))
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


@main_blueprint.route('/chat-to-<int:seller_id>')
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


def get_room(sid, cid):
    min_id, max_id = min(sid, cid), max(sid, cid)
    return '{}-{}'.format(min_id, max_id)


@socketio.on('join', namespace='/chat')
def join():
    print('join')
    sid = int(request.headers['Referer'].split('-')[2])
    room = get_room(sid, current_user.id)
    join_room(room)


@socketio.on('msg_to_server', namespace='/chat')
def message(data):
    msg = data.get('msg')
    print('server get message...', msg)
    cid = current_user.id
    sid = int(request.headers['Referer'].split('-')[2])
    room = get_room(sid, cid)
    if redis_server.lindex(room, 0):
        redis_server.rpushx(room, cid)
        redis_server.rpushx(room, msg)
    else:
        redis_server.rpush(room, cid, msg)

    emit('to_client', {'msg': msg, 'id': cid}, room=room)


@socketio.on('connect', namespace='/chat')
def connect():
    print('server connect...')


def msg_to_file(sid, cid):
    min_id, max_id = min(sid, cid), max(sid, cid)
    room = get_room(sid, cid)
    try:
        with open('./app/static/msgs/{}/{}.csv'.format(min_id, max_id), 'a', newline='') as csv_f:
            writer = csv.writer(csv_f)
            i = 0
            while i < redis_server.llen(room):
                writer.writerow([str(redis_server.lindex(room, i), encoding='utf-8'),
                                 str(redis_server.lindex(room, i + 1), encoding='utf-8')])
                i = i + 2
    finally:
        redis_server.delete(room)


@socketio.on('disconnect', namespace='/chat')
def disconnect():
    print('server disconnect', request.sid)


@socketio.on_error(namespace='/chat')
def chat_error_handler(e):
    print('An error has occurred: ' + str(e))


@socketio.on('unload', namespace='/chat')
def unload():
    print('close')
    sid = int(request.headers['Referer'].split('-')[2])
    global thread
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(msg_to_file, sid, current_user.id)

