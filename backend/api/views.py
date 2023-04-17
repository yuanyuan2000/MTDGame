from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import threading
from experiments.game import start

def start_game():
    start()

class StartGameView(APIView):
    def get(self, request):
        # Execute the main function of the game asynchronously using threads
        game_thread = threading.Thread(target=start_game)
        game_thread.start()

        return Response({"message": "Game started"}, status=status.HTTP_200_OK)

class NetworkDataView(APIView):
    def get(self, request, format=None):
        nodes = [
            {"id": 1, "label": "Node 1", "layer": 1, "x": 100, "y": 200, "color": {"background": "#FF0000"}, "value": 30},
            {"id": 2, "label": "Node 2", "layer": 1, "x": 50, "y": -250, "color": {"background": "#00FF00"}, "value": 30},
            {"id": 3, "label": "Node 3", "layer": 1, "x": 700, "y": 200, "color": {"background": "#0000FF"}, "value": 30},
        ]
        # edges = [
        #     {"from": 1, "to": 2},
        #     {"from": 2, "to": 3},
        #     {"from": 3, "to": 1},
        # ]
        edges = [
            {"id": 1, "from": 1, "to": 2},
            {"id": 2, "from": 2, "to": 3},
            {"id": 3, "from": 3, "to": 1},
        ]
        return Response({"nodes": nodes, "edges": edges})
