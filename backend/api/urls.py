from django.urls import path
# from .views import NodeList, EdgeList

# urlpatterns = [
#     path('nodes/', NodeList.as_view(), name='node-list'),
#     path('edges/', EdgeList.as_view(), name='edge-list'),
# ]

from .views import NetworkDataView

urlpatterns = [
    path('network_data/', NetworkDataView.as_view(), name='network-data'),
]
