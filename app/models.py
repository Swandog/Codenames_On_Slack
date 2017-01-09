from django.db import models

# Create your models here.
class Greeting(models.Model):
    when = models.DateTimeField('date created', auto_now_add=True)

class Game(models.Model):
    map_card = models.CharField(max_length=500, blank=True, default="")
    word_set = models.CharField(max_length=1000, blank=True, default="")
    channel_id = models.CharField(max_length=30, default=None)

class Player(models.Model):
    slack_id = models.CharField(max_length=30)
    team_color = models.CharField(max_length=4)
    is_spy_master = models.BooleanField(default=False)
    game_id = models.ForeignKey(Game, on_delete=models.CASCADE)
