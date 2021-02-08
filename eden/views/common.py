import json
import logging
import flask_login
import flask_restful as restful
from flask_login import login_required, current_user
from flask_restful import reqparse, fields, marshal_with
from flask import request, abort
from functools import wraps

from eden import app
from eden.model import *

api = restful.Api(app)


def batch_get(required: bool, src_dict: dict, *args):
    return {
        arg: src_dict[arg] if required else src_dict.get(arg)
        for arg in args
    }


def create_update_model(model: BaseModel):
    db.session.add(model)
    db.session.commit()


def delete_model(model: BaseModel):
    model.active = False
    db.session.add(model)
    db.session.commit()


def get_default_none(model, mid):
    return model.query.filter_by(id=mid).first()


class TimeItem(fields.Raw):
    def format(self, value):
        return value.strftime('%Y-%m-%d %H:%M:%S')


common_args = {
    'id': fields.Integer,
    'name': fields.String,
    'created': TimeItem(attribute='created'),
    'updated': TimeItem(attribute='updated'),
    'active': fields.Boolean,
    'description': fields.String,
    'extra': fields.String,
}

common_output = {
    'id': fields.Integer,
    'name': fields.String,
    'created': TimeItem(attribute='created'),
    'updated': TimeItem(attribute='updated'),
    'active': fields.Boolean,
    'description': fields.String,
    'extra': fields.String,
    'code': fields.Integer(default=200),
}


class BaseResource(restful.Resource):
    def __init__(self):
        super(BaseResource, self).__init__()
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('offset', type=int)
        self.parser.add_argument('limit', type=int)
        self.parser.add_argument('name', type=str)
        self.parser.add_argument('id', type=int)
        self.parser.add_argument('active', type=bool)
        self.parser.add_argument('description', type=str)
        self.parser.add_argument('extra', type=json)
        self.parser.add_argument('created', type=datetime)
        self.parser.add_argument('updated', type=datetime)
        self.args = {}

    def parse(self):
        self.args = self.parser.parse_args()


def fake_login(func):
    @wraps(func)
    def f_login(*args, **kwargs):
        # u = User.query.get(1)
        # flask_login.login_user(u, remember=True)
        return func(*args, **kwargs)

    return f_login
