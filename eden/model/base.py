from datetime import datetime
from flask_security import UserMixin, RoleMixin

from eden import db


class BaseModel(db.Model):
    __abstract__ = True
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(31), nullable=False, index=True)
    created = db.Column(db.DateTime, nullable=False, default=datetime.now)
    updated = db.Column(db.DateTime, nullable=False, onupdate=datetime.now, default=datetime.now)
    active = db.Column(db.Boolean(), nullable=False, default=True)
    description = db.Column(db.String(255), nullable=True)
    extra = db.Column(db.JSON, nullable=True)

    def __init__(self, **kwargs):
        super(BaseModel, self).__init__(**kwargs)

    def serialize(self):
        d = {}
        for col in self.__table__.columns:
            key = col.name
            value = getattr(self, key)
            if type(value) == datetime:
                value = datetime.strftime(value, '%Y-%m-%D')
            d[key] = value
        return d

    def deserialize(self, d: dict):
        return self.__init__(**d)

    def update(self, d: dict):
        [setattr(self, key, d[key]) for key in d]

    def update_(self, **kwargs):
        [setattr(self, key, kwargs[key]) for key in kwargs.keys()]


# relationship table
user_role = db.Table(
    'user_role',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('role_id', db.Integer, db.ForeignKey('role.id'), primary_key=True)
)

role_authority = db.Table(
    'role_authority',
    db.Column('role_id', db.Integer, db.ForeignKey('role.id'), primary_key=True),
    db.Column('authority_id', db.Integer, db.ForeignKey('authority.id'), primary_key=True)
)

manager_club = db.Table(
    'manager_club',
    db.Column('manager_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('club_id', db.Integer, db.ForeignKey('club.id'), primary_key=True)
)

member_club = db.Table(
    'member_club',
    db.Column('member_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('club_id', db.Integer, db.ForeignKey('club.id'), primary_key=True)
)

article_club = db.Table(
    'article_club',
    db.Column('article_id', db.Integer, db.ForeignKey('article.id'), primary_key=True),
    db.Column('club_id', db.Integer, db.ForeignKey('club.id'), primary_key=True)
)

visited_article = db.Table(
    'visited_article',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=False),
    db.Column('article_id', db.Integer, db.ForeignKey('article.id'), primary_key=False),
    db.Column('created', db.DateTime, nullable=False, default=datetime.utcnow())

)


# basic model
class User(BaseModel, UserMixin):
    school_number = db.Column(db.String(32), unique=True, index=True, nullable=False)
    email = db.Column(db.String(255), nullable=True)
    password = db.Column(db.String(255), nullable=False)
    sex = db.Column(db.Boolean, index=True, nullable=False, default=True)
    phone = db.Column(db.String(31), unique=True, nullable=True)

    roles = db.relationship(
        'Role',
        secondary=user_role,
        lazy=True,
        backref=db.backref('users', lazy='dynamic')
    )

    receive_messages = db.relationship(
        'Message',
        lazy=True,
        foreign_keys='Message.receiver_id',
        backref=db.backref('receiver', lazy=True)
    )

    send_message = db.relationship(
        'Message',
        lazy=True,
        foreign_keys='Message.user_id',
        backref=db.backref('sender', lazy=True),
    )

    public_article = db.relationship(
        'Article',
        lazy=True,
        foreign_keys='Article.user_id',
        backref=db.backref('public_user', lazy=True)
    )

    visited_articles = db.relationship(
        'VisitedHistory',
        lazy=True,
        foreign_keys='VisitedHistory.user_id',
        backref=db.backref('visited_users', lazy=True)
    )

    owning_clubs = db.relationship(
        'Club',
        lazy=True,
        backref=db.backref('owner', lazy=True)
    )

    membered_clubs = db.relationship(
        'Club',
        lazy=True,
        secondary=member_club,
        backref=db.backref('members', lazy=True)
    )

    managing_clubs = db.relationship(
        'Club',
        secondary=manager_club,
        lazy=True,
        backref=db.backref('managers', lazy=True)
    )
    publish_review = db.relationship(
        'Review',
        lazy=True,
        foreign_keys='Review.user_id',
        backref=db.backref('publisher', lazy=True)
    )
    receive_review = db.relationship(
        'Review',
        lazy=True,
        foreign_keys='Review.receiver_id',
        backref=db.backref('receiver', lazy=True)
    )

    @property
    def own_club_size(self):
        return len(self.owning_clubs)


class Role(BaseModel, RoleMixin):
    description = db.Column(db.String(255))
    authorities = db.relationship(
        'Authority',
        secondary=role_authority,
        lazy=True,
        backref=db.backref('roles', lazy=True)
    )


class Authority(BaseModel):
    description = db.Column(db.String(255))


class Message(BaseModel):
    context = db.Column(db.TEXT)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    source_id = db.Column(db.Integer, db.ForeignKey('message.id'), nullable=True)
    read = db.Column(db.Boolean, nullable=False, default=False)
    children_messages = db.relationship(
        'Message',
        lazy=True
    )
    join_id = db.Column(db.Integer, db.ForeignKey('club.id'), nullable=True)


class Article(BaseModel):
    context = db.Column(db.TEXT)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    tag_clubs = db.relationship(
        'Club',
        secondary=article_club,
        lazy=True,
        backref=db.backref('tag_article', lazy=True)
    )

    visited = db.relationship(
        'VisitedHistory',
        lazy=True,
        foreign_keys='VisitedHistory.article_id',
        backref=db.backref('visited_articles', lazy=True)
    )

    reviews = db.relationship(
        'Review',
        lazy=True,
        backref=db.backref('article', lazy=True)
    )


class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    created = db.Column(db.DateTime, nullable=False, default=datetime.now)
    updated = db.Column(db.DateTime, nullable=False, onupdate=datetime.now, default=datetime.now)
    active = db.Column(db.Boolean(), nullable=False, default=True)
    description = db.Column(db.String(255), nullable=True)
    extra = db.Column(db.JSON, nullable=True)
    context = db.Column(db.TEXT)
    approval = db.Column(db.Boolean)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    article_id = db.Column(db.Integer, db.ForeignKey('article.id'), nullable=False)

    parent_review_id = db.Column(db.Integer, db.ForeignKey('review.id'), nullable=True)
    children_reviews = db.relationship(
        'Review',
        lazy=True
    )


class Club(BaseModel):
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(31), nullable=False, index=True, unique=True)


class VisitedHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    article_id = db.Column(db.Integer, db.ForeignKey('article.id'), nullable=False)
    created = db.Column(db.DateTime, nullable=False, default=datetime.now)


class Verification(BaseModel):
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
