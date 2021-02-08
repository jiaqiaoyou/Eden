from .common import *
from .user import user_output

message_output = common_output.copy()
message_output.update({
    'context': fields.String,
    'sender': fields.Nested(user_output),
    'receiver': fields.Nested(user_output),
    'source_id': fields.Integer,
    'join_id': fields.Integer,
    'children_messages': fields.List(fields.Nested(message_output)),
    'extra': fields.Arbitrary,
    'read': fields.Boolean
})

message_page_output = {}
message_page_output.update({
    'code': fields.Integer(default=200),
    'total': fields.Integer,
    'has_next': fields.Boolean,
    'has_prev': fields.Boolean,
    'messages': fields.List(fields.Nested(message_output))
})


class MessageResource(BaseResource):
    def __init__(self):
        super(MessageResource, self).__init__()
        self.parser.add_argument('join_id', type=int, location='json')
        self.parser.add_argument('context', type=str, location='json')
        self.parser.add_argument('user_id', type=int)
        self.parser.add_argument('receiver_id', type=int)
        self.parser.add_argument('receive', type=bool, location='args')
        self.parser.add_argument('send', type=bool, location='args')
        self.parser.add_argument('school_numbers', type=str)
        self.parser.add_argument('sid', type=int, location='json')
        self.parser.add_argument('read', type=int, location='json')


class MessageListView(MessageResource):
    @fake_login
    @login_required
    @marshal_with(message_output)
    def post(self):
        u: User = current_user
        if not (u and u.active):
            abort(400, 'user not exist')
        self.parse()

        try:
            required = batch_get(True, self.args, 'name', 'context', 'school_numbers')
        except KeyError:
            abort(400, 'error parameters')

        if self.args.get('sid'):
            reply_msg: Message = Message.query.get_or_404(self.args['sid'])
        for school_number in required['school_numbers'].split(';'):
            m: Message = Message(name=required['name'],
                                 context=required['context'],
                                 receiver=User.query.filter_by(school_number=school_number).first_or_404(),
                                 user_id=current_user.id)
            sid, join_id = self.args.get('sid'), self.args.get('join_id')

            if join_id:
                m.join_id = join_id
            if sid:
                reply_source = Message.query.get_or_404(reply_msg.source_id) if reply_msg.source_id else reply_msg
                reply_source.children_messages.append(m)
            create_update_model(m)
        return 200

    @fake_login
    @login_required
    @marshal_with(message_page_output)
    def get(self):
        u: User = current_user
        if not (u and u.active):
            abort(400, 'user does not exist')

        self.parse()
        offset = self.args['offset'] if self.args['offset'] else 1
        limit = self.args['limit'] if self.args['limit'] else 50

        conditions = {'active': True}
        if self.args['send'] == 1:
            conditions.update({'user_id': u.id})
        elif self.args['receive'] == 1:
            conditions.update({'receiver_id': u.id})
        else:
            abort(400)

        filter_set = Message.query.filter_by(**conditions)
        page = filter_set.paginate(offset, limit)
        ret = [m for m in page.items]
        ret = sorted(ret, key=lambda i: i.created, reverse=True)
        return {
            'has_next': page.has_next,
            'has_prev': page.has_prev,
            'messages': ret,
            'total': filter_set.count()
        }


class MessageView(MessageResource):
    @login_required
    @marshal_with(message_output)
    def put(self, msg_id):

        u: User = current_user
        if not (u and u.active):
            abort(400)

        msg: Message = Message.query.get_or_404(msg_id)

        if msg.sender != u and msg.receiver != u:
            abort(403)

        self.parse()
        read = self.args.get('read')
        if read == 1:
            msg.read = True
        elif read == 0:
            msg.read = False

        create_update_model(msg)
        return msg

    @login_required
    @marshal_with(message_output)
    def get(self, msg_id):
        u: User = current_user
        if not (u and u.active):
            abort(400)

        msg: Message = Message.query.get_or_404(msg_id)

        if msg.sender != u and msg.receiver != u:
            abort(403)

        return msg


api.add_resource(MessageView, '/msg/<int:msg_id>')
api.add_resource(MessageListView, '/msg')
