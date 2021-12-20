from django.urls import path
from .views import *


urlpatterns = [
    path('create-batch/', tools_parser_batch_create, name="tools_parser_batch_create"),
    path('run-batch/<int:pk>/', tools_parser_batch_run, name="tools_parser_batch_run"),
    path('list-batch/', tools_parser_batch_list, name="tools_parser_batch_list"),
]
