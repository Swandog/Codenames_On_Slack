from django.db import models

# Create your models here.
class Greeting(models.Model):
    when = models.DateTimeField('date created', auto_now_add=True)

class Game(models.Model):
    map_card = models.CharField(max_length=500, blank=True, default="")
    word_set = models.CharField(max_length=1000, blank=True, default="")
    channel_id = models.CharField(max_length=30, default=None)
    game_master = models.CharField(max_length=30, default=None)
    accepting_new_players = models.BooleanField(default=True)
    current_team_playing = models.CharField(max_length=4, blank=True, default="")
    num_guesses_left = models.IntegerField(default=0)
    revealed_cards = models.CharField(max_length=200, blank=True, default="")

class Player(models.Model):
    slack_id = models.CharField(max_length=30, default=None)
    team_color = models.CharField(max_length=4, default=None)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    username = models.CharField(max_length=30, default=None)
    is_spymaster = models.BooleanField(default=False)
