# -*- coding:utf-8 -*-
# __author__ = 'Shanks'


import os

import sys

from app import create_app, db, socketio
from app.models import User, Role
from flask_script import Manager, Shell, Server
from flask_migrate import Migrate, MigrateCommand


app = create_app('default')
manager = Manager(app)
migrate = Migrate(app, db)

class Io_Server(Server):

    def __call__(self, app, host, port, use_debugger, use_reloader,
               threaded, processes, passthrough_errors):
        # we don't need to run the server in request context
        # so just run it directly

        if use_debugger is None:
            use_debugger = app.debug
            if use_debugger is None:
                use_debugger = True
                if sys.stderr.isatty():
                    print("Debugging is on. DANGER: Do not allow random users to connect to this server.", file=sys.stderr)
        if use_reloader is None:
            use_reloader = app.debug
        socketio.run(app=app,
                host=host,
                port=port,
                debug=use_debugger,
                use_debugger=use_debugger,
                use_reloader=use_reloader,
                #threaded=threaded,
                processes=processes,
                passthrough_errors=passthrough_errors,
                **self.server_options)

def make_shell_context():
    return dict(app=app, db=db, User=User, Role=Role)

manager.add_command('shell', Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)
manager.add_command('runserver', Io_Server())

if __name__ == '__main__':
    manager.run()
