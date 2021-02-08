from eden.model import *
import random

import math
from operator import itemgetter


class ItemBaseCF:
    def __init__(self):
        self.n_sim_article = 20
        self.n_rec_article = 10

        self.trainset = {}
        self.testset = {}

        self.article_sim_matrix = {}
        self.article_popular = {}
        self.article_count = 0

    def get_dataset(self, pivot=0.75):
        trainset_len = 0
        testset_len = 0

        for history in VisitedHistory.query.all():
            user_id = history.user_id
            article_id = history.article_id
            self.trainset.setdefault(user_id, {})
            self.trainset[user_id][article_id] = 1
            trainset_len += 1
            # if random.random() < pivot:
            #     self.trainset.setdefault(user_id, {})
            #     self.trainset[user_id][article_id] = 1
            #     trainset_len += 1
            # else:
            #     self.testset.setdefault(user_id, {})
            #     self.testset[user_id][article_id] = 1
            #     testset_len += 1

    def cal_article_sim(self):
        for user_id, article_ids in self.trainset.items():
            for article_id in article_ids:
                if article_id not in self.article_popular:
                    self.article_popular[article_id] = 0
                self.article_popular[article_id] += 1

        self.article_count = len(self.article_popular)

        for user_id, article_ids in self.trainset.items():
            for a1 in article_ids:
                for a2 in article_ids:
                    if a1 == a2:
                        continue
                    self.article_sim_matrix.setdefault(a1, {})
                    self.article_sim_matrix[a1].setdefault(a2, 0)
                    self.article_sim_matrix[a1][a2] += 1

        for a1, related_articles in self.article_sim_matrix.items():
            for a2, count in related_articles.items():
                if self.article_popular[a1] == 0 or self.article_popular[a2] == 0:
                    self.article_sim_matrix[a1][a2] = 0
                else:
                    self.article_sim_matrix[a1][a2] = count / math.sqrt(
                        self.article_popular[a1] * self.article_popular[a2]
                    )

    def recommend(self, user_id):
        K = self.n_sim_article
        N = self.n_rec_article
        rank = {}
        watched_articles = self.trainset[user_id]

        for article, rating in watched_articles.items():
            for related_article, w in sorted(self.article_sim_matrix[article].items(),
                                             key=itemgetter(1), reverse=True)[:K]:
                if related_article in watched_articles:
                    continue
                rank.setdefault(related_article, 0)
                rank[related_article] += w * float(rating)
        return sorted(rank.items(), key=itemgetter(1), reverse=True)[:N]

    def evaluate(self):
        N = self.n_rec_article
        # 准确率和召回率
        hit = 0
        rec_count = 0
        test_count = 0
        # 覆盖率
        all_rec_articles = set()

        for i, user in enumerate(self.trainset):
            test_articles = self.testset.get(user, {})
            rec_articles = self.recommend(user)
            for article, w in rec_articles:
                if article in test_articles:
                    hit += 1
                all_rec_articles.add(article)
            rec_count += N
            test_count += len(test_articles)

        precision = hit / (1.0 * rec_count)
        recall = hit / (1.0 * test_count)
        coverage = len(all_rec_articles) / (1.0 * self.article_count)


if __name__ == '__main__':
    item_cf = ItemBaseCF()
    item_cf.get_dataset()
    item_cf.cal_article_sim()

    user = User.query.get(1)
    print(item_cf.recommend(user.id))
