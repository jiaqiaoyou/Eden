from flask_socketio import emit, SocketIO
from flask import render_template
from flask_cors import CORS

from eden import app
from eden.admin import *
from eden.views import *

# cors = CORS(app, resources={r"/api/*": {"origins": "*"}})
socket_io = SocketIO(app, cors_allowed_origins="*")


@socket_io.on('message', namespace='/poll')
def poll(message):
    print('accept')
    emit('poll', {'msg': 'i am polling'})


@socket_io.on('connect')
def connect():
    print('connect')
    emit('after connect', {'data': 'connected!'})


if __name__ == '__main__':
    socket_io.run(app, port=4999)
