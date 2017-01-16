import os, random, json, requests, urllib, urlparse
from django.shortcuts import render
from django.http import HttpResponse

from .models import Greeting, Game, Player

# Create your views here.
def index(request):
    return render(request, 'index.html')

def test_webhook(request):
    req_dict = urlparse.parse_qs(urllib.unquote(request.body))
    print(req_dict)
    return HttpResponse(json.dumps({"text": "that seems to have done something! I'm not sure what..." }) content_type='application/json')


def db(request):
    greeting = Greeting()
    greeting.save()

    greetings = Greeting.objects.all()

    return render(request, 'db.html', {'greetings': greetings})

def initialize_game(request):
    # create a game instance in the db then let the users pick teams
    req_dict = urlparse.parse_qs(urllib.unquote(request.body))
    user_id = req_dict['user_id'][0]
    user_name = req_dict['user_name'][0]
    channel_id = req_dict['channel_id'][0]

    # if there's already an active game in the channel, respond with error
    if Game.objects.filter(channel_id=channel_id).count() > 0:
        payload = {"response_type": "ephemeral", "replace_original": False, "text": "There's already a game in progress!"}
    else:
        # create a new game in channel with the generated data
        game_board_data = generate_wordset()
        Game.objects.create(
            map_card = json.dumps(game_board_data["map_card"]),
            word_set = json.dumps(game_board_data["words_list"]),
            channel_id = channel_id,
            game_master = user_id
        )
        payload={
                "text": "<@{}> wants to play a game of Codenames".format(user_id, user_name),
                "response_type": "in_channel",
                "attachments": [
                    {
                        "text": "Choose a team",
                        "fallback": "You are unable to choose a game",
                        "callback_id": "team_chosen",
                        "color": "#3AA3E3",
                        "attachment_type": "default",
                        "actions": [
                            {
                                "name": "blue",
                                "text": "Blue Team",
                                "type": "button",
                                "value": "blue",
                            },
                            {
                                "name": "red",
                                "text": "Red Team",
                                "style": "danger",
                                "type": "button",
                                "value": "red",
                            }
                        ]
                    }
                ]
            }
    return HttpResponse(json.dumps(payload), content_type='application/json')

def close_teams(request):
    req_dict = urlparse.parse_qs(urllib.unquote(request.body))
    user_name = req_dict['user_name'][0]
    user_id = req_dict['user_id'][0]
    channel_id = req_dict['channel_id'][0]
    print(req_dict)

    # disable team selection, and let users pick their team captains
    if Game.objects.filter(channel_id=channel_id).count == 0:
        payload = {"text": "There's no active game in the channel, try `/codenames`."}
    else:
        active_game_in_channel = Game.objects.get(channel_id=channel_id)
        if user_id != active_game_in_channel.game_master:
            payload = {"text": "Only the game master (<@{}>) can close the teams.".format(active_game_in_channel.game_master)}
        else:
            # show buttons to pick team leaders
            buttons = []
            payload={
                    "text": "<@{}> wants to play a game of Codenames".format(user_id, user_name),
                    "response_type": "in_channel",
                    "attachments": [
                        {
                            "text": "Choose a team",
                            "fallback": "You are unable to choose a game",
                            "callback_id": "team_chosen",
                            "color": "#3AA3E3",
                            "attachment_type": "default",
                            "actions": [
                                {
                                    "name": "blue",
                                    "text": "Blue Team",
                                    "type": "button",
                                    "value": "blue",
                                },
                                {
                                    "name": "red",
                                    "text": "Red Team",
                                    "style": "danger",
                                    "type": "button",
                                    "value": "red",
                                }
                            ]
                        }
                    ]
                }

    return HttpResponse({json.dumps(payload)}, content_type='application/json')

def generate_wordset():
    # read the words_list file and build an array of words
    words = []
    words_file = open(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'words_list.txt'))
    for line in words_file:
        words.append(line.strip())
    total_num_words = len(words)

    # get 25 unique words at random from the list of words
    words_list = [words[idx] for idx in random.sample(range(0, total_num_words -1), 25)]
    starting_team = ["red", "blue"][random.randint(0,1)]
    map_card = generate_mapcard(starting_team)

    data = {"words_list": words_list, "map_card": map_card}

    return data


def generate_mapcard(starting_team):
    num_red_agents = 8
    num_blue_agents = 8

    # double agent
    if starting_team == "red":
        num_red_agents += 1
    else:
        num_blue_agents += 1

    ret = [""] * 25
    # generate 17 random indices (8 + 9 agents) for the 25 cards
    indices = random.sample(range(0, 24), 18)
    red_card_indices = indices[0: num_red_agents]
    blue_card_indices = indices[num_red_agents: 17]

    for red_idx in red_card_indices:
        ret[red_idx] = "R"
    for blue_idx in blue_card_indices:
        ret[blue_idx] = "B"

    #assassin card
    ret[indices[17]] = "X"

    return ret

def button(request):
    # parse the request to a dict
    req_dict = json.loads(urlparse.parse_qs(urllib.unquote(request.body))['payload'][0])
    actions = req_dict["actions"] #ex: [{u'name': u'chess', u'value': u'chess'}]
    callback_id = req_dict["callback_id"] #ex: wopr_game
    channel = req_dict["channel"] #ex: {u'id': u'C3NUEG0S0', u'name': u'game'}
    user = req_dict["user"] #ex: {u'id': u'U3N3Z66TB', u'name': u'dustin'}
    button_value = req_dict['actions'][0]['value']

    # detect if the user is picking a team
    if button_value == "blue" or button_value == "red":
        # prevent a player from adding themselves to the game multiple times
        active_game_in_channel = Game.objects.get(channel_id=channel['id'])
        if active_game_in_channel.accepting_new_players == False:
            payload = {'text': "Teams for this channel's active game have been locked.", "replace_original": False}
        else:
            if Player.objects.filter(slack_id=user['id'], game=active_game_in_channel).count() > 0:
                payload = {'text': "You've already been added to this game.", "replace_original": False}
            else:
                # create a to-be-deleted player object that fk's a player to the game instance
                Player.objects.create(
                    slack_id=user['id'],
                    team_color=button_value,
                    game=active_game_in_channel
                )
                payload = {'text': "added <@{}> to the {} team".format(user['name'], button_value), "replace_original": False, "response_type": "in_channel"}

    return HttpResponse(json.dumps(payload), content_type='application/json')
