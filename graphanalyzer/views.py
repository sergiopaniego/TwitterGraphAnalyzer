import json
import threading
from json import JSONDecodeError

from django.http import JsonResponse, HttpResponse
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
    try:
        data = json.load(json_data)
        return JsonResponse(data, safe=False)
    except:
        return HttpResponse('Decoding JSON has failed')


class GraphView(FormView, ListView):
    template_name = 'graphanalyzer/graph.html'
    context_object_name = 'graph'
    form_class = HashtagForm
    thread_started = False
    my_list = []

    def get_db_call(self, x):
        return {
            'pageRank': 'CALL algo.pageRank.stream(\'Tweet\', \'Relationship\', {iterations:5}) YIELD nodeId,'
                        ' score WITH * ORDER BY score DESC LIMIT 20 RETURN nodeId, score;',
            'betweenness': 'CALL algo.betweenness.stream(\'Tweet\',\'RELATED\',{direction:\'out\'})YIELD nodeId,'
                        ' centrality RETURN nodeId,centrality order by centrality desc limit 20;',
            'closeness': 'CALL algo.closeness.stream(\'Node\', \'LINKS\') YIELD nodeId, centrality RETURN nodeId,'
                        'centrality order by centrality desc limit 20;',
            'louvain': 'CALL algo.louvain.stream(\'Tweet\', \'RELATED\','
                        '{weightProperty:\'propertyName\', defaultValue:1.0, concurrency:4})'
                        ' YIELD nodeId, community '
                        ' RETURN nodeId, community LIMIT 20;'
        }.get(x, 1)

    def form_valid(self, form):
        if len(self.my_list) > 0:
            self.my_list[0].close_thread()
            self.my_list.pop()
        thread = TwitterThread(1, 'Twitter Thread', form)
        time.sleep(2)
        thread.start()
        self.my_list.append(thread)
        print('Number of threads ' + str(len(self.my_list)))
        return super().form_valid(form)

    def get_queryset(self):
        success_url = self.get_success_url()
        url = success_url.split("/")
        mode = url[len(url) - 1]
        mode = (self.get_db_call(mode))
        RefreshGraphThread(1, 'Refresh Thread', mode)


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


class RefreshGraphThread():
    def __init__(self, thread_id, name, mode):
        self.thread_id = thread_id
        self.name = name
        self.mode = mode
        self.run()

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
        try:
            nodes = json.load(open(filename))
            if type(self.mode) is not int:
                if len(self.mode.split('louvain')) < 2 :
                    print(self.mode)
                    nodes_communities = 1
                    try:
                        node_weights = json.dumps(graph.data(self.mode))
                    except ClientError as error:
                        print('ERROR: ' + error.message)
                        node_weights = 1
                elif len(self.mode.split('louvain')) == 2:
                    node_weights = 1
                    try:
                        nodes_communities = json.dumps(graph.data(self.mode))
                    except ClientError as error:
                        print('ERROR: ' + error.message)
                        nodes_communities = 1
            else:
                node_weights = 1
                nodes_communities = 1
            for idx, node in enumerate(nodes['nodes']):
                node['node']['nodeId'] = str(node['ID(node)'])
                if node_weights != 1:
                    try:
                        weight = self.get_node_weight(int(node['node']['nodeId']), node_weights)
                    except:
                        weight = 0
                else:
                    weight = 1
                if nodes_communities != 1:
                    try:
                        community = self.get_node_community(int(node['node']['nodeId']), nodes_communities)
                    except:
                        community = 20
                else:
                    community = 1
                node['node']['weight'] = str(weight)
                node['node']['community'] = str(community)
                tweets += json.dumps(node['node'])
                if (idx + 1) < len(nodes['nodes']):
                    tweets += ','
        except JSONDecodeError as error:
            print('Decoding JSON has failed ')
            print(error)
        except IndexError as error:
            print('Decoding JSON has failed')
            print(error)
        tweets += ']'
        return tweets

    def get_node_weight(self, node_id, node_weights):
        i = 0
        node = json.loads(json.dumps(json.loads(node_weights)[0]))
        while node['nodeId'] != node_id and i < 20:
            i += 1
            node = json.loads(json.dumps(json.loads(node_weights)[i]))
        try:
            return node['score']
        except KeyError:
            try:
                return node['centrality']
            except KeyError:
                return node['community']

    def get_node_community(self, node_id, nodes_communities):
        i = 0
        node = json.loads(json.dumps(json.loads(nodes_communities)[0]))
        while node['nodeId'] != node_id and i < 20:
            i += 1
            node = json.loads(json.dumps(json.loads(nodes_communities)[i]))
        return node['community']

    def get_links(self):
        graph = Graph(password=secrets.password)
        filename = "relationships.json"
        with open(filename, 'w') as outfile:
            outfile.write('{"links": ')
            json.dump(graph.data('MATCH (n)-[r]->(m) RETURN n,r,m;'), outfile)
            outfile.write('}')
        links = ', "links": ['
        try:
            relationships = json.load(open(filename))
            for idx, relationship in enumerate(relationships['links']):
                links += '{"source": ' + str(relationship['n']['id']) + ', "target": ' + str(
                    relationship['m']['id']) + '}'
                if (idx + 1) < len(relationships['links']):
                    links += ','
            links += ']}'
            return links
        except JSONDecodeError as error:
            print('Decoding JSON has failed')
            print(error)

    def run(self):
        print('Starting ' + self.name)
        filename = 'tweets.json'
        with open(filename, 'w') as outfile:
            outfile.write(self.get_nodes())
            outfile.write(self.get_links())
