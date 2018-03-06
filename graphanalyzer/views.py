from django.shortcuts import render
from .forms import HashtagForm
import graphanalyzer.twitterManager as twitterManager


def index(request):
    return render(request, 'graphanalyzer/index.html')

def graph(request):
    if request.method == 'POST':
        form = HashtagForm(request.POST)
        if form.is_valid():
            twitterManager.connectToStream(form.cleaned_data['hashtag'])
    return render(request, 'graphanalyzer/graph.html')