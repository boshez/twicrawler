import tweepy
import networkx as nx
import pqdict


class Crawler(object):
    def __init__(self, seed):
        # the larger the more important (reverse=True)
        self.crawl_frontier = pqdict.pqdict({user_id: 0 for user_id in seed}, reverse=True)
        self.visited = []
        self.graph = nx.DiGraph()

    def crawl(self, api, update_interval=5, max_itr=15):
        cnt = 0
        api.wait_on_rate_limit = True
        while cnt < max_itr:
            if not self.crawl_frontier:
                break

            user_id = self.crawl_frontier.pop()
            if user_id in self.visited:
                continue
            self.visited.append(user_id)

            status = api.get_user(user_id)
            if status.protected:
                continue
            print('user_id: %d, screen_name: %s' % (user_id, status.screen_name))

            friends = api.friends_ids(user_id)
            self.graph.add_edges_from([(user_id, friend) for friend in friends])
            self.crawl_frontier.update({friend: -1 for friend in friends if friend not in self.crawl_frontier})

            cnt += 1

            if cnt % update_interval == 0:
                ranks = nx.pagerank(self.graph)
                for key in self.crawl_frontier.keys():
                    if key in ranks:
                        self.crawl_frontier[key] = ranks[key]
