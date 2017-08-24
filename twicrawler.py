import networkx as nx
import pqdict


class Crawler(object):
    def __init__(self, api, seed):
        seed_dict = {user_id: 0 for user_id in seed}
        self.crawl_frontier = pqdict.pqdict(seed_dict, reverse=True)
        self.visited = []
        self.edges = []
        self.statuses = []
        self.api = api
        self.api.wait_on_rate_limit = True

    def _fetch_user(self, user_id):
        return self.api.get_user(user_id)

    def _fetch_friends_ids(self, user_id):
        return self.api.friends_ids(user_id)

    def _write_edges_csv(self, path):
        with open(path, 'a') as file:
            for item in self.edges:
                file.write("%d,%d\n" % item)

    def crawl(self, path, max_itr=15):
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
            self.crawl_frontier.update({user_id: 0 for user_id in friends})

            # updates priorities according to PageRank
            g = nx.from_edgelist(self.edges)
            ranks = nx.pagerank(g)
            for key in self.crawl_frontier.keys():
                if key in ranks:
                    self.crawl_frontier[key] = ranks[key]

            cnt += 1

        self._write_edges_csv(path)
