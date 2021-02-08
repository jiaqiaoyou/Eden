from flask_babelex import Babel
from flask import request, session
import json

from eden import app
from eden.admin import *
from eden.views import *

babel = Babel(app)


@babel.localeselector
def get_locale():
    if request.args.get('lang'):
        session['lang'] = request.args.get('lang')
    return session.get('lang', 'zh_CN')


if __name__ == '__main__':
    app.run()
