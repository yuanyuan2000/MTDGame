from django.urls import path
from .views import StartGameView, NetworkDataView

urlpatterns = [
    path('start_game/', StartGameView.as_view(), name='start-game'),
    path('network_data/', NetworkDataView.as_view(), name='network-data'),
]
