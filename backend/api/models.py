from django.db import models

class Node(models.Model):
    id = models.IntegerField(primary_key=True)
    layer = models.IntegerField()
    x = models.FloatField()
    y = models.FloatField()
    color = models.CharField(max_length=7)

class Edge(models.Model):
    source = models.ForeignKey(Node, on_delete=models.CASCADE, related_name='source_node')
    target = models.ForeignKey(Node, on_delete=models.CASCADE, related_name='target_node')
