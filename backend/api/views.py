from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import threading
from game import Game
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from rest_framework.decorators import api_view
# from .models import GameRoom
# from .serializers import GameRoomSerializer

game_instance = Game()

@api_view(['POST'])
def create_game_room(request):
    if request.method == 'POST':
        game_instance.set_game_mode(request.data['game_mode'])
        game_instance.set_creator_role(request.data['creator_role'])
        game_instance.set_room_id(request.data['room_id'])
        data = {
            'game_mode': request.data['game_mode'],
            'creator_role': request.data['creator_role'],
            'room_id': request.data['room_id']
        }
        return Response(data, status=201)



@api_view(['POST'])
def join_game_room(request):
    if request.method == 'POST':
        game_instance.set_opponent_role(request.data['opponent_role'])
        if game_instance.get_isrunning() and request.data['room_id'] == game_instance.get_room_id() and request.data['opponent_role'] != game_instance.get_creator_role():
            data = {
                'game_mode': game_instance.get_game_mode(),
                'opponent_role': game_instance.get_opponent_role(),
                'room_id': game_instance.get_room_id()
            }
            return Response(data, status=201)
        else:
            return Response(ValueError, status=400)


def start_game():
    # start the game
    if not game_instance.get_isrunning():
        game_instance.start()

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
        is_running = game_instance.get_isrunning()
        winner = game_instance.get_winner()
        time_used = game_instance.get_sim_time()
        total_time = game_instance.get_total_time()
        nodes = transform_nodes(game_instance.get_nodes())
        edges = transform_edges(game_instance.get_edges())
        return Response({"is_running": is_running, "winner": winner, "time_used": time_used, "total_time": total_time, "nodes": nodes, "edges": edges})
    
class NetworkDataView2(APIView):
    def get(self, request, format=None):
        is_running = game_instance.get_isrunning()
        winner = game_instance.get_winner()
        time_used = game_instance.get_sim_time()
        total_time = game_instance.get_total_time()
        nodes = transform_nodes(game_instance.get_nodes())
        edges = transform_edges(game_instance.get_edges())
        visible_hosts = game_instance.get_visible_hosts()
        return Response({"is_running": is_running, "winner": winner, "time_used": time_used, "total_time": total_time, "nodes": nodes, "edges": edges, "visible_hosts": visible_hosts})


@csrf_exempt
def clicked_node(request):
    try:
        if request.method == 'POST':
            data = json.loads(request.body)
            node_id = data['nodeId']
            node_info = game_instance.get_host_info(node_id)
            print("Node info:", node_info)
            return JsonResponse({"nodeinfo": node_info}, status=200)
        else:
            return JsonResponse({"message": "Invalid request"}, status=400)
    except TypeError as e:
        return JsonResponse(str(e))
    
@csrf_exempt
def ip_shuffling(request):
    try:
        if request.method == 'POST':
            data = json.loads(request.body)
            node_id = data['nodeId']
            is_shuffled = game_instance.ip_shuffling(node_id)  # execute IP shuffling
            return JsonResponse({"is_shuffled": is_shuffled}, status=200)
        else:
            return JsonResponse({"message": "Invalid request"}, status=400)
    except TypeError as e:
        return JsonResponse(str(e), status=400)
    
@csrf_exempt
def topological_shuffling(request):
    try:
        if request.method == 'POST':
            data = json.loads(request.body)
            # node_id = data['nodeId']
            is_shuffled = game_instance.topology_shuffle()
            return JsonResponse({"is_shuffled": is_shuffled}, status=200)
        else:
            return JsonResponse({"message": "Invalid request"}, status=400)
    except TypeError as e:
        return JsonResponse(str(e), status=400)
    
@csrf_exempt
def os_diversity(request):
    try:
        if request.method == 'POST':
            data = json.loads(request.body)
            # node_id = data['nodeId']
            is_sucessful = game_instance.os_diversity()
            return JsonResponse({"is_sucessful": is_sucessful}, status=200)
        else:
            return JsonResponse({"message": "Invalid request"}, status=400)
    except TypeError as e:
        return JsonResponse(str(e), status=400)
    
@csrf_exempt
def service_diversity(request):
    try:
        if request.method == 'POST':
            data = json.loads(request.body)
            node_id = data['nodeId']
            is_sucessful = game_instance.service_diversity(node_id)
            return JsonResponse({"is_sucessful": is_sucessful}, status=200)
        else:
            return JsonResponse({"message": "Invalid request"}, status=400)
    except TypeError as e:
        return JsonResponse(str(e), status=400)
    
@csrf_exempt
def get_details(request):
    try:
        if request.method == 'POST':
            data = json.loads(request.body)
            node_id = data['nodeId']
            all_details = game_instance.get_host_all_details(node_id)
            return JsonResponse({"all_details": all_details}, status=200)
        else:
            return JsonResponse({"message": "Invalid request"}, status=400)
    except TypeError as e:
        return JsonResponse(str(e), status=400)
    

@csrf_exempt
def enum_host(request):
    try:
        if request.method == 'POST':
            data = json.loads(request.body)
            node_id = data['nodeId']
            enum_host_list = game_instance.enum_host()
            return JsonResponse({"enum_host_list": enum_host_list}, status=200)
        else:
            return JsonResponse({"message": "Invalid request"}, status=400)
    except TypeError as e:
        return JsonResponse(str(e), status=400)
    
@csrf_exempt
def scan_port(request):
    try:
        if request.method == 'POST':
            data = json.loads(request.body)
            node_id = data['nodeId']
            scan_port_result = game_instance.scan_port(node_id)
            return JsonResponse({"scan_port_result": scan_port_result}, status=200)
        else:
            return JsonResponse({"message": "Invalid request"}, status=400)
    except TypeError as e:
        return JsonResponse(str(e), status=400)
    
@csrf_exempt
def exploit_vuln(request):
    try:
        if request.method == 'POST':
            data = json.loads(request.body)
            node_id = data['nodeId']
            exploit_vuln_result = game_instance.exploit_vuln(node_id)
            return JsonResponse({"exploit_vuln_result": exploit_vuln_result}, status=200)
        else:
            return JsonResponse({"message": "Invalid request"}, status=400)
    except TypeError as e:
        return JsonResponse(str(e), status=400)
    
@csrf_exempt
def brute_force(request):
    try:
        if request.method == 'POST':
            data = json.loads(request.body)
            node_id = data['nodeId']
            brute_force_result = game_instance.brute_force(node_id)
            return JsonResponse({"brute_force_result": brute_force_result}, status=200)
        else:
            return JsonResponse({"message": "Invalid request"}, status=400)
    except TypeError as e:
        return JsonResponse(str(e), status=400)
