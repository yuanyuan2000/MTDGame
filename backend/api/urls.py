from django.urls import path
from . import views
from .views import StartGameView, NetworkDataView, clicked_node, ip_shuffling, topological_shuffling

urlpatterns = [
    path('create_game_room/', views.create_game_room, name='create_game_room'),
    path('join_game_room/', views.join_game_room, name='join_game_room'),
    path('start_game/', StartGameView.as_view(), name='start-game'),
    path('network_data/', NetworkDataView.as_view(), name='network-data'),
    path('network_data/clicked_node/', clicked_node, name='clicked_node'),
    path('network_data/ip_shuffling/', ip_shuffling, name='ip_shuffling'),
    path('network_data/topological_shuffling/', topological_shuffling, name='topological_shuffling'),
]
