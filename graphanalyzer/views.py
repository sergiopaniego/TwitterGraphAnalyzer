import json
import threading

from django.http import JsonResponse
from django.shortcuts import render
from django.views.generic import ListView
from py2neo import Graph, ClientError
import secrets
from .forms import HashtagForm
import graphanalyzer.twitterManager as twitterManager
from django.views.generic.edit import FormView
import time


def index(request):
    return render(request, 'graphanalyzer/index.html')


def load_json(request):
    json_data = open('tweets.json')
    data = json.load(json_data)
    return JsonResponse(data, safe=False)


myList = []


class GraphView(FormView, ListView):
    template_name = 'graphanalyzer/graph.html'
    context_object_name = 'graph'
    form_class = HashtagForm
    thread_started = False

    def get_db_call(self, x):
        return {
            'pageRank': 'CALL algo.pageRank.stream(\'Tweet\', \'Relationship\', {iterations:5}) YIELD nodeId,'
                        ' score WITH * ORDER BY score DESC LIMIT 20 RETURN nodeId, score;',
            'betweenness': 'CALL algo.betweenness.stream(\'Tweet\',\'RELATED\',{direction:\'out\'})YIELD nodeId,'
                           ' centrality RETURN nodeId,centrality order by centrality desc limit 20;',
            'closeness': 'CALL algo.closeness.stream(\'Node\', \'LINKS\') YIELD nodeId, centrality RETURN nodeId,'
                         'centrality order by centrality desc limit 20;',
        }.get(x, 1)

    def form_valid(self, form):
        if len(myList) > 0:
            myList[0].close_thread()
            myList.pop()
        thread = TwitterThread(1, 'Twitter Thread', form)
        time.sleep(2)
        thread.start()
        myList.append(thread)
        print('Number of threads ' + str(len(myList)))
        return super().form_valid(form)

    def get_queryset(self):
        success_url = self.get_success_url()
        url = success_url.split("/")
        mode = url[len(url) - 1]
        mode = (self.get_db_call(mode))
        thread = RefreshGraphThread(1, 'Refresh Thread', mode)
        time.sleep(1)
        thread.start()
        graph = Graph(password=secrets.password)
        return graph.data('MATCH(n) RETURN n')


class TwitterThread(threading.Thread):
    def __init__(self, thread_id, name, form):
        threading.Thread.__init__(self)
        self.thread_id = thread_id
        self.name = name
        self.form = form

    def run(self):
        print('Starting ' + self.name)
        twitterManager.connect_to_stream(self.form.cleaned_data['hashtag'])
        print('Exiting ' + self.name)

    def close_thread(self):
        twitterManager.close_thread()


class RefreshGraphThread(threading.Thread):
    def __init__(self, thread_id, name, mode):
        threading.Thread.__init__(self)
        self.thread_id = thread_id
        self.name = name
        self.mode = mode

    def check_tweet_text(self, tweet):
        new_tweet = ''
        for idx, char in enumerate(tweet):
            if char == '"':
                new_tweet += '\\"'
            else:
                new_tweet += char
        return new_tweet

    def get_nodes(self):
        graph = Graph(password=secrets.password)
        filename = 'nodes.json'
        with open(filename, 'w') as outfile:
            outfile.write('{"nodes": ')
            json.dump(graph.data('MATCH (node) RETURN (node),ID(node)'), outfile)
            outfile.write('}')
        tweets = '{"nodes": ['
        nodes = json.load(open(filename))

        if type(self.mode) is not int:
            try:
                node_weights = json.dumps(graph.data(self.mode))
            except ClientError:
                node_weights = 1
        else:
            node_weights = 1
        for idx, node in enumerate(nodes['nodes']):
            node['node']['nodeId'] = str(node['ID(node)'])
            if node_weights != 1:
                weight = self.get_node_weight(int(node['node']['nodeId']), node_weights)
            else:
                weight = 1
            node['node']['weight'] = str(weight)
            tweets += json.dumps(node['node'])
            if (idx + 1) < len(nodes['nodes']):
                tweets += ','
        tweets += ']'
        return tweets

    def get_node_weight(self, node_id, node_weights):
        i = 0
        node = json.loads(json.dumps(json.loads(node_weights)[0]))
        while node['nodeId'] != node_id:
            i += 1
            node = json.loads(json.dumps(json.loads(node_weights)[i]))
        try:
            return node['score']
        except KeyError:
            return node['centrality']

    def get_links(self):
        graph = Graph(password=secrets.password)
        filename = "relationships.json"
        with open(filename, 'w') as outfile:
            outfile.write('{"links": ')
            json.dump(graph.data('MATCH (n)-[r]->(m) RETURN n,r,m;'), outfile)
            outfile.write('}')
        links = ', "links": ['
        relationships = json.load(open(filename))
        for idx, relationship in enumerate(relationships['links']):
            links += '{"source": ' + str(relationship['n']['id']) + ', "target": ' + str(
                relationship['m']['id']) + ', "value": 1}'
            if (idx + 1) < len(relationships['links']):
                links += ','
        links += ']}'
        return links

    def run(self):
        print('Starting ' + self.name)
        while True:
            filename = 'tweets.json'
            with open(filename, 'w') as outfile:
                outfile.write(self.get_nodes())
                outfile.write(self.get_links())
            self.get_links()
            time.sleep(5)
