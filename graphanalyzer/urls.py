from django.urls import path

from . import views

app_name = 'graphanalyzer'
urlpatterns = [
    path('', views.index, name='index'),
    path('graph', views.GraphView.as_view(success_url="graph"), name='graph')
]