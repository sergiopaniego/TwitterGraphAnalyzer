import threading
from django.shortcuts import render
from django.views.generic import ListView
from py2neo import Graph
import secrets
from .forms import HashtagForm
import graphanalyzer.twitterManager as twitterManager
from django.views.generic.edit import FormView


def index(request):
    return render(request, 'graphanalyzer/index.html')

class GraphView(FormView, ListView):
    template_name = 'graphanalyzer/graph.html'
    context_object_name = 'graph'
    form_class = HashtagForm

    def form_valid(self, form):
        # This method is called when valid form data has been POSTed.
        # It should return an HttpResponse.
        thread1 = myThread(1, "Thread-1", form)
        thread1.start()
        return super().form_valid(form)

    def get_queryset(self):
        graph = Graph(password=secrets.password)
        return graph.data("MATCH (a:Person) RETURN a.name, a.born LIMIT 4")

    '''
    def graph(self, **kwargs):
        if request.method == 'POST':
            form = HashtagForm(request.POST)
            if form.is_valid():
                thread1 = myThread(1, "Thread-1", form)
                thread1.start()
        return render(request, 'graphanalyzer/graph.html')
    '''

class myThread(threading.Thread):
    def __init__(self, threadID, name, form):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.form = form

    def run(self):
        print("Starting " + self.name)
        twitterManager.connectToStream(self.form.cleaned_data['hashtag'])
        print("Exiting " + self.name)