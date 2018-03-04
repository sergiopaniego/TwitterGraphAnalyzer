from django.http import HttpResponse
from django.shortcuts import render


def index(request):
    return render(request, 'graphanalyzer/index.html')

def graph(request):
    return HttpResponse("Hello, world. This is the detail page")