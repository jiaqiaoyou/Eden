from .common import *
from .user import user_output

club_output = common_output.copy()
club_output.update({
    'owner': fields.Nested(user_output),
    'managers': fields.List(fields.Nested(user_output)),
    'members': fields.List(fields.Nested(user_output)),

    'owning': fields.Boolean,
    'managing': fields.Boolean,
    'membering': fields.Boolean
})

club_page_output = {}
club_page_output.update({
    'code': fields.Integer(default=200),
    'total': fields.Integer,
    'has_next': fields.Boolean,
    'has_prev': fields.Boolean,
    'clubs': fields.List(fields.Nested(club_output))
})


class ClubResource(BaseResource):
    def __init__(self):
        super(ClubResource, self).__init__()
        self.parser.add_argument('me', type=int)
        self.parser.add_argument('owner_id', type=int)
        self.parser.add_argument('manager_ids', type=list, location='json')
        self.parser.add_argument('member_ids', type=list, location='json')
        self.parser.add_argument('inclub', type=int)
        self.parser.add_argument('outclub', type=int)
        self.parser.add_argument('kick', type=int)
        self.parser.add_argument('join', type=int)
        self.parser.add_argument('join_id', type=int, location='json')
        self.parser.add_argument('user_id', type=int, location='json')
        self.parser.add_argument('role_info', type=int)


class ClubListView(ClubResource):
    # @fake_login
    @login_required
    @marshal_with(club_page_output)
    def get(self):
        u: User = current_user
        if not (u and u.active):
            abort(400, 'user does not exist')

        self.parse()
        offset = self.args['offset'] if self.args['offset'] else 1
        limit = self.args['limit'] if self.args['limit'] else 50

        conditions = {'active': True}
        if self.args['me'] == 1:
            conditions.update({'owner_id': u.id})
        filter_set = Club.query.filter_by(**conditions)
        total = filter_set.count()
        search_owner, search_club = request.args.get('search_owner'), request.args.get('search_club')
        if search_owner:
            filter_set = filter_set.filter_by(owner=User.query.filter_by(name=search_owner).first())
        if search_club:
            filter_set = filter_set.filter(Club.name.like('%' + search_club + '%'))
        page = filter_set.paginate(offset, min(limit, total - offset + 1))
        return {
            'has_next': page.has_next,
            'has_prev': page.has_prev,
            'clubs': [c for c in page.items],
            'total': filter_set.count()
        }

    # @fake_login
    @login_required
    @marshal_with(club_output)
    def post(self):
        u: User = current_user
        if not (u and u.active):
            abort(400, 'user does not exist')

        self.parse()
        try:
            required = batch_get(True, self.args, 'name')
            required['owner_id'] = u.id
            non_required = batch_get(False, self.args, 'extra', 'description')
        except KeyError:
            abort(400, 'error parameters')

        if Club.query.filter_by(name=required['name']).first():
            abort(400, 'club already exist')

        club = Club(**required, **non_required)
        club.managers.append(current_user)
        club.members.append(current_user)
        create_update_model(club)

        return club, 200


class ClubView(ClubResource):
    # @fake_login
    @login_required
    @marshal_with(club_output)
    def get(self, club_id):
        self.parse()
        u: User = current_user
        if not u or not u.active:
            return {'msg': 'user does not exist'}, 400

        club = Club.query.get_or_404(club_id)

        if self.args.get('role_info') == 1:
            return {
                'owning': current_user == club.owner,
                'managing': current_user in club.managers,
                'membering': current_user in club.members
            }
        if self.args.get('outclub') == 1:
            club.members.remove(current_user)
            create_update_model(club)
            return 200
        return club

    # @fake_login
    @login_required
    @marshal_with(club_output)
    def put(self, club_id):
        u: User = current_user
        club = Club.query.get_or_404(club_id)
        if not u or not u.active:
            abort(400, 'user does not exist')
        if u not in club.managers and u != club.owner:
            abort(403, 'no authorize')
        self.parse()
        try:
            owner_only = batch_get(False, self.args, 'owner_id', 'manager_ids')
            if not owner_only.get('owner_id'):
                owner_only['owner_id'] = u.id
            manager_only = batch_get(False, self.args, 'name', 'member_ids', 'description', 'name', 'extra')
        except KeyError:
            abort(400, 'error parameters')

        members = club.members
        managers = club.managers

        if self.args.get('kick') == 1:
            kick_user: User = User.query.get(self.args['user_id'])
            club.members.remove(kick_user)
            create_update_model(club)
            return 200
        if self.args.get('join') == 1:
            join_user: User = User.query.get_or_404(request.args['join_id'])
            club.members.append(join_user)
            create_update_model(club)
            return 200
        if manager_only['member_ids']:
            for uid in manager_only['member_ids']:
                u = User.query.filter_by(id=uid).first()
                if u:
                    members.append(u)

        if owner_only['manager_ids']:
            for mid in owner_only['manager_ids']:
                u = User.query.filter_by(id=mid).first()
                if u:
                    managers.append(u)

        owner_only.update({'managers': managers})
        manager_only.update({'members': members})
        if u == club.owner:
            club.update_(**owner_only, **manager_only)
        elif u in club.managers:
            club.update_(**owner_only)

        create_update_model(club)
        return club, 200

    # @fake_login
    @login_required
    @marshal_with(club_output)
    def delete(self, club_id):
        u: User = current_user

        club = Club.query.get_or_404(club_id)

        if u != club.owner:
            return {'no authority'}, 403

        db.session.delete(club)
        db.session.commit()

        return 200


api.add_resource(ClubListView, '/club')
api.add_resource(ClubView, '/club/<int:club_id>')
