from django.urls import include, path
from django.contrib import admin

urlpatterns = [
    path('analyzer/', include('graphanalyzer.urls')),
    path('admin/', admin.site.urls),
]