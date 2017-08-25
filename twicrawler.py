import tweepy
import networkx as nx
import pqdict


class Crawler(object):
    def __init__(self, api, seed):
        self.api = api
        self.api.wait_on_rate_limit = True
        # the larger the more important (reverse=True)
        self.crawl_frontier = pqdict.pqdict({user_id: 0 for user_id in seed}, reverse=True)
        self.visited = []
        self.edges = []
        self.graph = nx.DiGraph()

    def _fetch_user(self, user_id):
        return self.api.get_user(user_id)

    def _fetch_friends_ids(self, user_id):
        return self.api.friends_ids(user_id)

    def crawl(self, update_interval=5, max_itr=15):
        cnt = 0
        while cnt < max_itr:
            if not self.crawl_frontier:
                break

            user_id = self.crawl_frontier.pop()
            if user_id in self.visited:
                continue
            self.visited.append(user_id)

            status = self._fetch_user(user_id)
            if status.protected:
                continue
            print('user_id: %d, screen_name: %s' % (user_id, status.screen_name))

            friends = self._fetch_friends_ids(user_id)
            self.edges.extend([(user_id, friend) for friend in friends])
            self.crawl_frontier.update({friend: -1 for friend in friends if friend not in self.crawl_frontier})

            cnt += 1

            if cnt % update_interval == 0:
                self.graph.add_edges_from(self.edges)
                self.edges[:] = []
                ranks = nx.pagerank(self.graph)
                for key in self.crawl_frontier.keys():
                    if key in ranks:
                        self.crawl_frontier[key] = ranks[key]
