from django.urls import path
from . import views
from .views import StartGameView, NetworkDataView, clicked_node, ip_shuffling, topological_shuffling, os_diversity, service_diversity, get_details
from .views import NetworkDataView2, enum_host, scan_port, exploit_vuln, brute_force
urlpatterns = [
    path('create_game_room/', views.create_game_room, name='create_game_room'),
    path('join_game_room/', views.join_game_room, name='join_game_room'),
    path('start_game/', StartGameView.as_view(), name='start-game'),
    path('defender/network_data/', NetworkDataView.as_view(), name='network-data'),
    path('defender/network_data/clicked_node/', clicked_node, name='clicked_node'),
    path('defender/network_data/ip_shuffling/', ip_shuffling, name='ip_shuffling'),
    path('defender/network_data/topological_shuffling/', topological_shuffling, name='topological_shuffling'),
    path('defender/network_data/os_diversity/', os_diversity, name='os_diversity'),
    path('defender/network_data/service_diversity/', service_diversity, name='service_diversity'),
    path('defender/network_data/get_details/', get_details, name='get_details'),
    path('attacker/network_data/', NetworkDataView2.as_view(), name='network-data'),
    path('attacker/network_data/enum_host/', enum_host, name='enum_host'),
    path('attacker/network_data/scan_port/', scan_port, name='scan_port'),
    path('attacker/network_data/exploit_vuln/', exploit_vuln, name='exploit_vuln'),
    path('attacker/network_data/brute_force/', brute_force, name='brute_force'),
]
