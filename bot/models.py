from django.db import models

# Create your models here.

class Chat(models.Model):
    chat_id = models.IntegerField()
    active_game = models.TextField(default="None")
    attempts_number_game = models.IntegerField(default=3)
    number_number_game = models.IntegerField(default=0)
    

class Member(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name="member")
    name = models.TextField()
    games_won = models.IntegerField(default=0)
    attempts = models.IntegerField(default=0)


