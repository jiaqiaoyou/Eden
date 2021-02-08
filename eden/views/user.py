from werkzeug.security import generate_password_hash, check_password_hash

from .common import *
from flask_sqlalchemy import BaseQuery

logger = logging.getLogger(__name__)
user_output = common_output.copy()
user_output.update(
    {
        'school_number': fields.String,
        'email': fields.String,
        'sex': fields.Boolean,
        'phone': fields.String,
        'readall': fields.Boolean
    }
)

from ._user import _user_output


class UserResource(BaseResource):
    def __init__(self):
        super(UserResource, self).__init__()
        self.parser.add_argument('school_number', type=str)
        self.parser.add_argument('email', type=str)
        self.parser.add_argument('password', type=str)
        self.parser.add_argument('sex', type=bool)
        self.parser.add_argument('phone', type=str)
        self.parser.add_argument('name', type=str)


class UserView(UserResource):

    @fake_login
    @login_required
    @marshal_with(_user_output)
    def get(self, user_id):
        return User.query.get_or_404(user_id, 'user not found')

    @fake_login
    @login_required
    @marshal_with(user_output)
    def put(self, user_id):
        self.parse()
        u = User.query.get_or_404(user_id, 'user not found')

        if u != current_user:
            abort(403, 'no authority')

        try:
            if self.args.get('password'):
                self.args['password'] = generate_password_hash(self.args['password'])
            for key in self.args:
                if self.args[key]:
                    setattr(u, key, self.args[key])
        except KeyError:
            return {'msg': 'error parameters'}, 400

        create_update_model(u)
        return u, 200

    @fake_login
    @login_required
    @marshal_with(user_output)
    def delete(self, user_id):
        u = User.query.get_or_404(user_id)
        delete_model(u)
        return u, 200


class UserListView(UserResource):
    @fake_login
    @login_required
    @marshal_with(user_output)
    def get(self):
        self.parse()
        return [u for u in User.query.paginate(self.args['offset'], self.args['limit']).items]

    @fake_login
    @login_required
    @marshal_with(user_output)
    def post(self):
        self.parse()
        try:
            create_dict = batch_get(True, self.args, 'name', 'sex', 'phone', 'school_number', 'password')
        except KeyError:
            return {'msg': 'error parameters'}, 400
        u = User(**create_dict)
        u.password = generate_password_hash(u.password)
        create_update_model(u)
        return u, 200


class IndexView(restful.Resource):
    @classmethod
    def get(cls):
        return {'hello': 'world'}


class MeView(UserResource):
    @login_required
    @marshal_with(_user_output)
    def get(self):
        u: User = current_user
        if not (u and u.active):
            abort(400)
        return u

    @login_required
    @marshal_with(user_output)
    def post(self):
        pass


class LogoutView(UserResource):
    @login_required
    @marshal_with(user_output)
    def post(self):
        u: User = current_user
        if not (u and u.active):
            abort(400)
        flask_login.logout_user()
        return 200


class LoginView(UserResource):
    @fake_login
    @marshal_with(user_output)
    def post(self):
        self.parse()
        try:
            school_number, password = batch_get(True, self.args, 'school_number', 'password').values()
        except KeyError:
            return {'msg': 'error parameters', 'code': 400}

        u = User.query.filter_by(school_number=school_number).first_or_404()
        if not check_password_hash(u.password, password):
            return {'msg': 'error password', 'code': 400}
        flask_login.login_user(u, remember=True)
        return u, 200


class ReadAll(UserResource):
    @login_required
    @marshal_with(user_output)
    def get(self, user_id):
        u: User = current_user
        for msg in u.receive_messages:
            if not msg.read:
                return {'readall': False}
        return {'readall': True}


api.add_resource(ReadAll, '/readall/<int:user_id>')
api.add_resource(IndexView, '/')
api.add_resource(UserListView, '/user')
api.add_resource(UserView, '/user/<int:user_id>')
api.add_resource(LoginView, '/user/login')
api.add_resource(MeView, '/user/me')
api.add_resource(LogoutView, '/user/logout')
