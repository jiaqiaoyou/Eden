from .common import *
from .article import article_output
from .user import user_output

review_output = common_output.copy()
review_output.update({
    'context': fields.String,
    'approval': fields.Boolean,
    'publisher': fields.Nested(user_output),
    'receiver': fields.Nested(user_output),
    'article': fields.Nested(article_output),
    'children_reviews': fields.List(fields.Nested(review_output))
})

review_page_output = {}
review_page_output.update({
    'code': fields.Integer(default=200),
    'total': fields.Integer,
    'has_next': fields.Boolean,
    'has_prev': fields.Boolean,
    'reviews': fields.List(fields.Nested(review_output)),
    'article': fields.Nested(article_output)
})


class ReviewResource(BaseResource):
    def __init__(self):
        super(ReviewResource, self).__init__()
        self.parser.add_argument('context', type=str, location='json')
        self.parser.add_argument('approval', type=bool, location='json')
        self.parser.add_argument('article_id', type=int)
        self.parser.add_argument('receiver_id', type=int, location='json')
        self.parser.add_argument('from_article', type=int, location='args')
        self.parser.add_argument('from_user', type=bool, location='args')
        self.parser.add_argument('parent_review_id', type=int, location='json')
        self.parser.add_argument('send', type=int)
        self.parser.add_argument('receive', type=int)


class ReviewView(ReviewResource):
    @fake_login
    @login_required
    @marshal_with(review_output)
    def get(self, rw_id):
        u: User = current_user
        if not (u and u.active):
            abort(400)
        review = Review.query.get_or_404(rw_id)
        return review

    @fake_login
    @login_required
    @marshal_with(review_output)
    def put(self, rw_id):
        u: User = current_user
        if not (u and u.active):
            abort(400)
        review = Review.query.get_or_404(rw_id)
        if u != review.user:
            abort(403)

        self.parse()
        try:
            required = batch_get(True, self.args, 'context', 'name', 'approval', 'article_id')
            required['user_id'] = u.id
            non_required = batch_get(False, self.args, 'description', 'extra')
        except KeyError:
            abort(400)

        review.update_(**required, **non_required)
        create_update_model(review)

    @fake_login
    @login_required
    @marshal_with(review_output)
    def delete(self, rw_id):
        u: User = current_user
        if not (u and u.active):
            abort(400)
        review = Review.query.get_or_404(rw_id)
        if u != review.user:
            abort(403)
        review.active = False
        create_update_model(review)


class ReviewListView(ReviewResource):
    @login_required
    @marshal_with(review_output)
    def post(self):
        u: User = current_user
        if not (u and u.active):
            abort(400)

        self.parse()
        try:
            required = batch_get(True, self.args, 'context', 'approval', 'article_id', 'receiver_id')
            required['user_id'] = u.id
            non_required = batch_get(False, self.args, 'description', 'extra')
        except KeyError:
            abort(400)

        review = Review(**required, **non_required)
        parent_id = self.args.get('parent_review_id')
        if parent_id:
            parent = Review.query.get_or_404(parent_id)
            real_parent = parent if parent.parent_review_id is None else Review.query.get_or_404(parent.parent_review_id)
            real_parent.children_reviews.append(review)
            create_update_model(real_parent)
        create_update_model(review)
        return review

    @login_required
    @marshal_with(review_page_output)
    def get(self):
        u: User = current_user
        if not (u and u.active):
            abort(400, 'user does not exist')

        self.parse()
        offset = self.args['offset'] if self.args['offset'] else 1
        limit = self.args['limit'] if self.args['limit'] else 50

        conditions = {'active': True, 'parent_review_id': None}
        if self.args.get('send') == 1:
            conditions.update({'user_id': u.id})
        elif self.args.get('receive') == 1:
            conditions.update({'receiver_id': u.id})
        elif self.args.get('article_id'):
            conditions.update({'article_id': self.args['article_id']})
            art = Article.query.get(self.args['article_id'])
        else:
            abort(400)
        filter_set = Review.query.filter_by(**conditions)
        page = filter_set.paginate(offset, limit)
        return {
            'has_next': page.has_next,
            'has_prev': page.has_prev,
            'reviews': [r for r in page.items],
            'total': filter_set.count(),
            'article': art
        }


api.add_resource(ReviewView, '/review/<int:rw_id>')
api.add_resource(ReviewListView, '/review')
