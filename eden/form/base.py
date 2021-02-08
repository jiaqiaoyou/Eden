from wtforms import form, fields, validators
from werkzeug.security import check_password_hash
from eden.model import db, User


class LoginForm(form.Form):
    school_number = fields.StringField(
        label='学号',
        validators=[
            validators.required(),
            validators.Length(max=15)
        ]
    )
    password = fields.PasswordField(
        label='密码',
        validators=[
            validators.required(),
            validators.Length(max=32)
        ]
    )

    def get_user(self):
        print(db.session.query(User))
        return db.session.query(User) \
            .filter_by(school_number=self.school_number.data) \
            .first()

    def validate_login(self, authority_name):
        user = self.get_user()

        if user is None:
            raise validators.ValidationError('invalid user')
        if not check_password_hash(user.password, self.password.data):
            raise validators.ValidationError('invalid password')

        for role in user.roles:
            if authority_name in [auth.name for auth in role.authorities]:
                return

        raise validators.ValidationError('no permission')


# if debug
class RegistrationForm(form.Form):
    req = [validators.required()]
    school_number = fields.StringField(validators=req)
    name = fields.StringField(validators=req)
    password = fields.PasswordField(validators=req)
    email = fields.StringField(validators=req)
    active = True
