import json
import threading

from django.http import JsonResponse
from django.shortcuts import render
from django.views.generic import ListView
from py2neo import Graph
import secrets
from .forms import HashtagForm
import graphanalyzer.twitterManager as twitterManager
from django.views.generic.edit import FormView
import time


def index(request):
    return render(request, 'graphanalyzer/index.html')


def loadjson(request):
    json_data = open('tweets.json')
    data = json.load(json_data)
    return JsonResponse(data, safe=False)

myList = []


class GraphView(FormView, ListView):
    template_name = 'graphanalyzer/graph.html'
    context_object_name = 'graph'
    form_class = HashtagForm
    thread_started = False

    def form_valid(self, form):
        # This method is called when valid form data has been POSTed.
        # It should return an HttpResponse.
        if len(myList) > 0:
            myList[0].closeThread()
            myList.pop()
        thread = TwitterThread(1, "Twitter Thread", form)
        time.sleep(2)
        thread.start()
        myList.append(thread)
        print("Number of threads " + str(len(myList)))
        return super().form_valid(form)

    def get_queryset(self):
        thread = RefreshGraphThread(1, "Refresh Thread")
        time.sleep(1)
        thread.start()
        graph = Graph(password=secrets.password)
        return graph.data("MATCH(n) RETURN n")

    '''
        "{\"nodes\": " + graph.data("MATCH (n) RETURN (n)") +   "\"links\": []}"
        MATCH (n)-[r]->(m),(o) RETURN n,r,m,o;
        MATCH (n)-[r]->(m) RETURN n,r,m;
        MATCH(n) RETURN n;
    '''


class TwitterThread(threading.Thread):
    def __init__(self, threadID, name, form):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.form = form

    def run(self):
        print("Starting " + self.name)
        twitterManager.connectToStream(self.form.cleaned_data['hashtag'])
        print("Exiting " + self.name)

    def closeThread(self):
        twitterManager.closeThread()


class RefreshGraphThread(threading.Thread):
    def __init__(self, threadID, name):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name

    def run(self):
        print("Starting " + self.name)
        while (True):
            graph = Graph(password=secrets.password)
            filename = "tweets.json"
            with open(filename, 'w') as outfile:
                outfile.write("{\"nodes\": ")
                json.dump(graph.data("MATCH (n) RETURN (n)"), outfile)
                outfile.write(", \"links\": []}")
            time.sleep(5)
        print("Exiting " + self.name)
