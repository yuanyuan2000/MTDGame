from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import threading
from experiments.game import Game

game_instance = Game()
game_instance.start() 

def start_game():
    # start the game
    # new_game = Game()
    # new_game.start()
    pass

class StartGameView(APIView):
    def get(self, request):
        # Execute the main function of the game asynchronously using threads
        game_thread = threading.Thread(target=start_game)
        game_thread.start()

        return Response({"message": "Game started"}, status=status.HTTP_200_OK)
    
def transform_nodes(old_nodes):
    # print('-------------',type(old_nodes))
    new_nodes = []
    for node in old_nodes:
        new_node = {
            "id": node.id,
            "label": str(node.id),
            "layer": 1,
            "x": node.x,
            "y": node.y,
            "color": {"background": str(node.color)},
            "value": 30,
        }
        new_nodes.append(new_node)
        # print(new_node)
    return new_nodes

def transform_edges(edges):
    transformed_edges = []
    for idx, edge in enumerate(edges, start=1):
        transformed_edges.append({
            "id": idx,
            "from": edge[0],
            "to": edge[1]
        })
    return transformed_edges

class NetworkDataView(APIView):
    def get(self, request, format=None):
        nodes = transform_nodes(game_instance.get_nodes())
        edges = transform_edges(game_instance.get_edges())
        return Response({"nodes": nodes, "edges": edges})
