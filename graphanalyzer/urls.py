from django.urls import path

from . import views

app_name = 'graphanalyzer'
urlpatterns = [
    path('', views.index, name='index'),
    path('graph', views.GraphView.as_view(success_url="graph"), name='graph'),
    path('graph/pageRank', views.GraphView.as_view(success_url="graph/pageRank"), name='pageRank'),
    path('graph/betweenness', views.GraphView.as_view(success_url="graph/betweenness"), name='betweenness'),
    path('graph/closeness', views.GraphView.as_view(success_url="graph/closeness"), name='closeness'),
    path('graph/tweets.json', views.load_json, name='load_json'),
    path('tweets.json', views.load_json, name='load_json')
]
