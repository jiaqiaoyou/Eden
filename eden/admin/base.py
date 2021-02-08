import flask_login as login
from flask import redirect, url_for, request
from flask_admin import expose, AdminIndexView, Admin, helpers
from flask_admin.contrib import sqla
from werkzeug.security import generate_password_hash

from eden import app
from eden.model import *
from eden.form import LoginForm, RegistrationForm

login_manager = login.LoginManager(app)


@login_manager.user_loader
def load_user(user_id):
    return db.session.query(User).get(user_id)


class IndexView(AdminIndexView):
    @expose('/')
    def index(self):
        if not login.current_user.is_authenticated:
            return redirect(url_for('.login_view'))
        link = '<a href="' + url_for('.logout_view') + '">退出登陆</a>'
        self._template_args['name'] = app.config['NAME']
        self._template_args['user_name'] = login.current_user.name
        self._template_args['link'] = link
        return super(IndexView, self).index()

    @expose('/login/', methods=['GET', 'POST'])
    def login_view(self):
        form = LoginForm(request.form)
        if helpers.validate_form_on_submit(form):
            user = form.get_user()
            form.validate_login('control_all')
            login.login_user(user)
            print(user, user.is_active, login.current_user)

        if login.current_user.is_authenticated:
            return redirect(url_for('.index'))

        link = '<p>没有帐号? <a href="' + url_for('.register_view') + '">点此注册</a></p>'
        self._template_args['form'] = form
        self._template_args['link'] = link
        return self.render('index.html')

    @expose('/register/', methods=('GET', 'POST'))
    def register_view(self):
        form = RegistrationForm(request.form)
        if helpers.validate_form_on_submit(form):
            user = User()

            form.populate_obj(user)
            user.password = generate_password_hash(form.password.data)
            user.roles.append(Role.query.get(1))
            db.session.add(user)
            db.session.commit()

            login.login_user(user)
            return redirect(url_for('.index'))
        link = '<p>已有帐号? <a href="' + url_for('.login_view') + '">点此登陆.</a></p>'
        self._template_args['form'] = form
        self._template_args['link'] = link
        return self.render('index.html')

    @expose('/logout/')
    def logout_view(self):
        login.logout_user()
        return redirect(url_for('.index'))


admin = Admin(
    app=app,
    name=app.config['NAME'],
    index_view=IndexView()
)


class BaseModelView(sqla.ModelView):
    column_labels = {
        'name': '名称 ',
        'created': '创建时间',
        'updated': '更新时间',
        'active': '状态',
        'school_number': '学号',
        'email': '邮箱',
        'password': '密码',
        'description': '描述',
        'message': '消息',
        'approval': '是否赞同',
        'context': '正文',
        'user': '用户',
        'owner': '所有者',
        'receiver': '接受者',
        'club': '社团',
        'authorities': '权限集',
        'users': '用户集',
        'roles': '角色集',
        'messages': '消息',
        'managers': '管理者',
        'members': '成员',
        'reviews': '点评',
        'article': '文章',
        'articles': '文章',
        'receive_messages': '接受的消息',
        'send_message': '发送的消息',
        'public_article': '发布的文章',
        'owning_clubs': '拥有的社团',
        'managing_clubs': '管理的社团',
        'membered_clubs': '加入的社团'
    }
    form_excluded_columns = ('created', 'updated')


class AdminView(BaseModelView):

    def is_accessible(self):
        return login.current_user.is_authenticated and \
               'super_user' in [role.name for role in login.current_user.roles]

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('admin.login_view', next=request.url))


class UserModelView(AdminView):
    form_create_rules = ('name', 'school_number', 'email', 'password', 'active')

    def on_model_change(self, form, model, is_created):
        model.password = generate_password_hash(form.data['password'])


def from_dict(data, *args):
    return (data[arg] for arg in args)


def add_views(*args):
    for arg in args:
        if len(arg) == 3:
            model, func, name = arg[0], arg[1], arg[2]
        else:
            model, func, name = arg[0], AdminView, arg[1]
        admin.add_view(func(model, db.session, name=name))


add_views(
    (User, UserModelView, '用户'),
    (Role, '角色'),
    (Authority, '权限'),
    (Club, '社团'),
    (Message, '消息'),
    (Review, '点评'),
    (Article, '文章'),
    (VisitedHistory, sqla.ModelView, '浏览记录'),
    (Verification, '验证码')
)
