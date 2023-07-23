from django.db import models
# from django.contrib.auth.models import User


# class GameRoom(models.Model):
#     room_id = models.AutoField(primary_key=True)
#     creator = models.CharField(max_length=100, default='', blank=True)
#     opponent = models.CharField(max_length=100, default='', blank=True)
#     game_mode = models.CharField(max_length=20)
#     creator_role = models.CharField(max_length=20)
#     opponent_role = models.CharField(max_length=20, null=True, blank=True)



# class Node(models.Model):
#     id = models.IntegerField(primary_key=True)
#     layer = models.IntegerField()
#     x = models.FloatField()
#     y = models.FloatField()
#     color = models.CharField(max_length=7)

# class Edge(models.Model):
#     source = models.ForeignKey(Node, on_delete=models.CASCADE, related_name='source_node')
#     target = models.ForeignKey(Node, on_delete=models.CASCADE, related_name='target_node')
