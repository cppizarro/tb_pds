from django.db import models

# Create your models here.

class Chat(models.Model):
    chat_id = models.IntegerField()
    active_game = models.TextField(default="None")
    

# class Member(models.Model):
#     group = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name="member")
#     games_won = models.IntegerField(default=0)


