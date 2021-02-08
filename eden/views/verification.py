from .common import *

import random
import string
import smtplib
from email.mime.text import MIMEText
from werkzeug.security import generate_password_hash


def generate() -> str:
    ran_str = ''.join(random.sample(string.ascii_letters + string.digits, 4)).encode('utf-8').strip()
    return ran_str


def send(code: str, email: str):
    mail_host = 'smtp.qq.com'
    mail_user = '1765955084'
    mail_pass = 'dqkhyxfuwzsadfgc'
    sender = '1765955084@qq.com'
    receivers = [email]

    message = MIMEText(code, 'plain', 'utf-8')
    message['Subject'] = '华南农业大学社团系统验证邮件'
    message['From'] = sender
    message['To'] = receivers[0]

    try:
        smtpObj = smtplib.SMTP()
        # 连接到服务器
        smtpObj.connect(mail_host, 25)
        # 登录到服务器
        smtpObj.login(mail_user, mail_pass)
        # 发送
        msg = message.as_string()
        smtpObj.sendmail(
            sender, receivers, msg)
        # 退出
        smtpObj.quit()
        print('success')
    except smtplib.SMTPException as e:
        print('error', e)  # 打印错误


class VerificationView(BaseResource):
    def post(self):
        school_number = request.json.get('school_number')
        code = request.json.get('code')
        u: User = User.query.filter_by(school_number=school_number).first()
        if not (u and u.active):
            abort(400)
        v: Verification = Verification.query.filter_by(user_id=u.id).first()
        if v and v.name.decode() == code:
            return {'code': 200}
        return {'code': 400}

    def get(self):
        school_number = request.args.get('school_number')
        u: User = User.query.filter_by(school_number=school_number).first()
        if not (u and u.active):
            abort(400)
        verification: Verification = Verification.query.filter_by(user_id=u.id).first()
        if not verification:
            verification = Verification(user_id=u.id, name=generate())
        else:
            verification.name = generate()
        create_update_model(verification)
        send(verification.name, u.email)
        return {'code': 200}


class ForgetView(BaseResource):
    def post(self):
        school_number = request.json.get('school_number')
        password = request.json.get('pass')
        u: User = User.query.filter_by(school_number=school_number).first()
        if not (u and u.active):
            abort(400)
        u.password = generate_password_hash(password)
        create_update_model(u)
        return {'code': 200}


api.add_resource(ForgetView, '/forget')
api.add_resource(VerificationView, '/verification')
