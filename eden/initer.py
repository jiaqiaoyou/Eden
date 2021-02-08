from eden.model import *
from werkzeug.security import generate_password_hash

db.drop_all()
db.create_all()
r = Role(
    name='super_user',
    description='role with access to admin'
)
u = User(
    name='jiaqiao.you',
    school_number='1',
    email='1694388549@qq.com',
    password=generate_password_hash('1'),
    description='all of one',
    sex=True,
    phone='110'
)
a = Authority(
    name='control_all',
    description='control all'
)
u.roles.append(r)
r.authorities.append(a)
db.session.add(a)
db.session.add(r)
db.session.add(u)
db.session.commit()
