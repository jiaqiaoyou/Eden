from .common import *
from .user import user_output
from .club import club_output

article_output = common_output.copy()
article_output.update(
    {
        'context': fields.String,
        'owner': fields.Nested(user_output, attribute='public_user'),
        'tag_clubs': fields.List(fields.Nested(club_output))
    }
)
article_page_output = {}
article_page_output.update({
    'code': fields.Integer(default=200),
    'total': fields.Integer,
    'has_next': fields.Boolean,
    'has_prev': fields.Boolean,
    'articles': fields.List(fields.Nested(article_output))
})


class ArticleResource(BaseResource):
    def __init__(self):
        super(ArticleResource, self).__init__()
        self.parser.add_argument('context', type=str)
        self.parser.add_argument('user_id', type=int)
        self.parser.add_argument('tag_clubs_dict', type=list, location='body')
        self.parser.add_argument('club_id', type=int)
        self.parser.add_argument('me', type=int)


class ArticleListView(ArticleResource):
    @login_required
    @marshal_with(article_page_output)
    def get(self):
        u: User = current_user
        if not (u and u.active):
            abort(400, 'user does not exist')

        self.parse()
        offset = self.args['offset'] if self.args['offset'] else 1
        limit = self.args['limit'] if self.args['limit'] else 50

        conditions = {'active': True}
        filter_name = request.args.get('name')
        filter_owner = request.args.get('owner')
        filter_clubs = request.args.get('clubs')
        if self.args['me'] == 1:
            conditions.update({'user_id': u.id})
        filter_set = Article.query.filter_by(**conditions)
        total = filter_set.count()
        if filter_name and filter_name != '':
            filter_set = filter_set.filter(Article.name.like('%' + filter_name + '%'))
        if filter_owner and filter_owner != '':
            filter_set = filter_set.filter_by(public_user=User.query.filter_by(name=filter_owner).first())
        page = filter_set.paginate(offset, min(limit,total-offset+1))
        ret = [a for a in page.items]
        final_ret = []
        if filter_clubs and filter_clubs != '':
            filter_club = Club.query.get_or_404(int(filter_clubs))
            for r in ret:
                if filter_club in r.tag_clubs:
                    final_ret.append(r)
        else:
            final_ret = ret
        return {
            'has_next': page.has_next,
            'has_prev': page.has_prev,
            'articles': final_ret,
            'total': filter_set.count()
        }

    @login_required
    @marshal_with(article_output)
    def post(self):
        u = current_user
        if not u or not u.active:
            return {'msg': 'user does not exist'}, 400
        self.parse()

        try:
            required_dict = batch_get(True, self.args, 'name', 'context')
            required_dict['user_id'] = u.id
            non_required_dict = batch_get(False, self.args, 'description', 'extra')

            required_dict.update(
                {'tag_clubs': [Club.query.get_or_404(club) for club in request.json['tag_clubs_dict']]})
        except KeyError:
            return {'msg': 'parameters error'}, 400

        art = Article(**required_dict, **non_required_dict)
        create_update_model(art)


class ArticleView(ArticleResource):
    @fake_login
    @login_required
    @marshal_with(article_output)
    def get(self, article_id):
        u: User = current_user
        if not u or not u.active:
            return {'msg': 'user does not exist'}, 400
        art = Article.query.get_or_404(article_id)

        history = VisitedHistory(user_id=u.id, article_id=article_id)
        create_update_model(history)
        create_update_model(u)
        return art

    @fake_login
    @login_required
    @marshal_with(article_output)
    def put(self, article_id):
        self.parse()
        art: Article = Article.query.get_or_404(article_id)

        try:
            required = batch_get(True, self.args, 'context', 'club_id', 'name')
            non_required = batch_get(False, self.args, 'description', 'extra')

            if request.json.get('tag_clubs_dict'):
                required.update({'tag_clubs': [Club.query.get_or_404(club) for club in request.json['tag_clubs_dict']]})
        except KeyError:
            return {'msg': 'parameters error'}, 400

        art.update_(**required, **non_required)
        create_update_model(art)

    @fake_login
    @login_required
    @marshal_with(article_output)
    def delete(self, article_id):
        art = Article.query.get_or_404(article_id, 'article does not exist')
        art.active = False
        create_update_model(art)


class Recommend(ArticleResource):
    @login_required
    @marshal_with(article_page_output)
    def get(self):
        import random
        ret = [art for art in Article.query.all()][0:10]
        random.shuffle(ret)
        return {
            'articles': ret,

        }


api.add_resource(Recommend, '/recommend')
api.add_resource(ArticleListView, '/article')
api.add_resource(ArticleView, '/article/<int:article_id>')
