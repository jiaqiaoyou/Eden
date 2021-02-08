import random
import string
import smtplib
from email.mime.text import MIMEText


def send(code: str, email: str):
    mail_host = 'smtp.qq.com'
    mail_user = '1765955084'
    mail_pass = 'dqkhyxfuwzsadfgc'
    sender = '1765955084@qq.com'
    receivers = [email]

    message = MIMEText('你的验证码为：' + code, 'plain', 'utf-8')
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
        smtpObj.sendmail(
            sender, receivers, message.as_string())
        # 退出
        smtpObj.quit()
        print('success')
    except smtplib.SMTPException as e:
        print('error', e)  # 打印错误


send('1234', '1694388549@qq.com')
