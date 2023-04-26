from django.urls import path
from .views import StartGameView, NetworkDataView, clicked_node

urlpatterns = [
    path('start_game/', StartGameView.as_view(), name='start-game'),
    path('network_data/', NetworkDataView.as_view(), name='network-data'),
    path('network_data/clicked_node/', clicked_node, name='clicked_node'),
]
