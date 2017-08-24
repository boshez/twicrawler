import tweepy
import networkx as nx
import pqdict


class Crawler(object):
    def __init__(self, config, seed):
        seed_dict = {user_id: 0 for user_id in seed}
        # the larger the more important (reverse=True)
        self.crawl_frontier = pqdict.pqdict(seed_dict, reverse=True)
        self.visited = []
        self.edges = []
        self.graph = None
        self.statuses = []
        self._auth_api(config)

    def _auth_api(self, config):
        auth = tweepy.OAuthHandler(config.consumer_key, config.consumer_secret)
        auth.set_access_token(config.access_token_key, config.access_token_secret)
        self.api = tweepy.API(auth)
        self.api.wait_on_rate_limit = True

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
            self.statuses.append(status)
            print('user_id: %d, screen_name: %s' % (user_id, status.screen_name))

            friends = self._fetch_friends_ids(user_id)
            self.edges.extend([(user_id, friend) for friend in friends])
            self.crawl_frontier.update({friend: -1 for friend in friends})

            cnt += 1

            if cnt % update_interval == 0:
                self.graph = nx.from_edgelist(self.edges)
                ranks = nx.pagerank(self.graph)
                for key in self.crawl_frontier.keys():
                    if key in ranks:
                        # the smaller the more important
                        self.crawl_frontier[key] = ranks[key]
