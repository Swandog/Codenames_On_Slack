import os, random, json, requests, urllib, urlparse
from django.shortcuts import render
from django.http import HttpResponse
from urllib2 import Request, urlopen, URLError
from .models import Greeting, Game, Player

color_emoji_map = {"R": ":red_circle", "B": ":large_blue_circle:", "X": ":black_circle:"}

# Create your views here.
def index(request):
    return render(request, 'index.html')

def test_webhook(request):
    req_dict = urlparse.parse_qs(urllib.unquote(request.body))
    print(req_dict)
    return HttpResponse(json.dumps({"text": "That seems to have done something! I'm not sure what..." }), content_type='application/json')


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
            current_team_playing = game_board_data["starting_team"],
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

    if Player.objects.filter(game__channel_id=channel_id).count() < 4:
        return HttpResponse({"text": "There needs to be at least 4 players for a game."}, content_type='application/json')

    # disable team selection, and let users pick their team captains
    if Game.objects.filter(channel_id=channel_id).count == 0:
        payload = {"text": "There's no active game in the channel, try `/codenames`."}
    else:
        active_game_in_channel = Game.objects.get(channel_id=channel_id)
        if active_game_in_channel.accepting_new_players == False:
            return HttpResponse({"text": "Teams are closed for the current game."}, content_type='application/json')
        if user_id != active_game_in_channel.game_master:
            payload = {"text": "Only the game master (<@{}>) can finalize the teams.".format(active_game_in_channel.game_master)}
        else:
            active_game_in_channel.accepting_new_players = False
            # show buttons to pick team leaders
            actions = []
            for blue_player in Player.objects.filter(team_color='blue'):
                actions.append({
                    "name": "blue_spymaster",
                    "text": blue_player.username,
                    "type": "button",
                    "value": blue_player.slack_id
                })
            payload = {
                "text": "<@{}>, choose a Spymaster (clue-giver) for the *Blue* team.".format(active_game_in_channel.game_master),
                "response_type": "in_channel",
                "attachments": [
                    {
                        "fallback": "unable to choose spymaster",
                        "callback_id": "spymaster_chosen",
                        "color": "#3AA3E3",
                        "attachment_type": "default",
                        "actions": actions
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
    staring_team = determine_starting_team(map_card)

    data = {"words_list": words_list, "map_card": map_card, "starting_team": starting_team}

    return data

def determine_starting_team(map_card):
        r_count = 0
        b_count = 0
        for card in map_card:
            if card == "R":
                r_count += 1
            elif card == "B":
                b_count += 1
        if r_count > b_count:
            return "red"
        else:
            return "blue"

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

def show_map_card(request):
    # restricted to users who are flagged as spymasters for the game
    req_dict = urlparse.parse_qs(urllib.unquote(request.body))
    channel_id = req_dict['channel_id'][0]
    user_id = req_dict['user_id'][0]

    if Game.objects.filter(channel_id=channel_id).count() == 0:
        payload = {'text': "There is no active game in this channel, try `/codenames`"}
    else:
        active_game = Game.objects.get(channel_id=channel_id)
        if Player.objects.filter(slack_id=user_id).count() == 0:
            payload = {'text': "You aren't currently in a game of Codenames."}
        elif Player.objects.get(slack_id=user_id).is_spymaster == False:
            payload = {'text': "You aren't flagged as a spymaster for the current game."}
        else:
            map_card = json.loads(active_game.map_card)
            word_set = json.loads(active_game.word_set)
            attachments = []
            actions = []
            for (idx, color) in enumerate(map_card):
                btn_style = ""
                if color == "R":
                    btn_style = "danger"
                    btn_text = word_set[idx]
                elif color == "B":
                    btn_style = "primary"
                    btn_text = word_set[idx]
                elif color == "X":
                    btn_text = "*{}*".format(word_set[idx])
                else:
                    btn_text = word_set[idx]
                actions.append({
                    "name": "map_card",
                    "text": ":large_blue_circle: {}".format(btn_text),
                    "type": "button",
                    "value": "map_card",
                    "style": btn_style
                })
            for x in range(1,6):
                attachments.append(
                    {
                        "fallback": "error displaying mapcard",
                        "callback_id": "red map_card shown",
                        "color": "#3AA3E3",
                        "attachment_type": "default",
                        "actions": actions[(x-1)*5:x*5]
                    }
                )
            payload = {
                "text": "Here's the map card!",
                "attachments": attachments
            }

    return HttpResponse(json.dumps(payload), content_type='application/json')

def button(request):
    # parse the request to a dict
    req_dict = json.loads(urlparse.parse_qs(urllib.unquote(request.body))['payload'][0])
    actions = req_dict["actions"] #ex: [{u'name': u'chess', u'value': u'chess'}]
    callback_id = req_dict["callback_id"] #ex: wopr_game
    channel = req_dict["channel"] #ex: {u'id': u'C3NUEG0S0', u'name': u'game'}
    user = req_dict["user"] #ex: {u'id': u'U3N3Z66TB', u'name': u'dustin'}
    button_value = req_dict['actions'][0]['value']
    button_name = req_dict['actions'][0]['name']

    active_game_in_channel = Game.objects.get(channel_id=channel['id'])

    # detect if the user is picking a team
    print(button_name)
    if button_name == "blue" or button_name == "red":
        payload = handle_team_selection(active_game_in_channel, channel, user, button_value)
    elif button_name == "blue_spymaster":
        payload = handle_blue_spymaster_selection(active_game_in_channel, channel, user, button_value)
    elif button_name == "red_spymaster":
        payload = handle_red_spymaster_selection(active_game_in_channel, channel, user, button_value)
    elif button_name == "map_card":
        payload = {'text': "Good job!", "replace_original": False}
    elif button_name == "card":
        payload = {'text': button_value, 'replace_original': Fla}

    return HttpResponse(json.dumps(payload), content_type='application/json')

def handle_team_selection(active_game, channel, user, button_value):
    # prevent a player from adding themselves to the game multiple times
    if active_game.accepting_new_players == False:
        payload = {'text': "Teams for this channel's active game have been locked.", "replace_original": False}
    else:
        if Player.objects.filter(slack_id=user['id'], game=active_game).count() > 0:
            payload = {'text': "You've already been added to this game.", "replace_original": False}
        else:
            # create a to-be-deleted player object that fk's a player to the game instance
            Player.objects.create(
                slack_id=user['id'],
                username=user['name'],
                team_color=button_value,
                game=active_game
            )
            payload = {'text': "added <@{}> to the {} team".format(user['name'], button_value), "replace_original": False, "response_type": "in_channel"}

    return payload

def handle_blue_spymaster_selection(active_game, channel, user, button_value):
    # assert the person who clicked the button is the spymaster
    if active_game.game_master != user['id']:
        payload = {"text": "Only the game master (<@{}) can set a spymaster", "replace_original": False}
    else:
        Player.objects.filter(game__channel_id=channel['id'], slack_id=button_value).update(is_spymaster=True)
        actions = []
        for red_player in Player.objects.filter(team_color='red'):
            actions.append({
                "name": "red_spymaster",
                "text": red_player.username,
                "type": "button",
                "value": red_player.slack_id
            })
        payload =  {
                "text": "<@{}> was set as the Blue spymaster, now choose the *Red* spymaster.".format(button_value),
                "response_type": "in_channel",
                "attachments": [
                    {
                        "fallback": "unable to choose spymaster",
                        "callback_id": "spymaster_chosen",
                        "color": "#3AA3E3",
                        "attachment_type": "default",
                        "actions": actions
                    }
                ]
            }
    return payload

def handle_red_spymaster_selection(active_game, channel, user, button_value):
    if active_game.game_master != user['id']:
        payload = {"text": "Only the game master (<@{}) can set a spymaster", "replace_original": False}
    else:
        Player.objects.filter(game__channel_id=channel['id'], slack_id=button_value).update(is_spymaster=True)
        # teams and spymasters have been chosen, show the board
        actions = []
        attachments = []
        word_set = json.loads(active_game.word_set)
        map_card = json.loads(active_game.map_card)
        for (idx, word) in enumerate(word_set):
            actions.append({
                "name": "card",
                "text": color_emoji_map[map_card[idx]] + word,
                "type": "button",
                "value": map_card[idx]
            })
        for x in range(1, 6):
            attachments.append(
                {
                    "fallback": "error picking card",
                    "callback_id": "card_chosen",
                    "attachment_type": "default",
                    "actions": actions[(x-1)*5:x*5]
                }
            )
        payload = {
            "text": "Here's the board. {} team goes first!".format(active_game.current_team_playing),
            "response_type": "in_channel",
            "attachments": attachments
        }

    return payload

def give_hint(request):
    req_dict = urlparse.parse_qs(urllib.unquote(request.body))
    user_name = req_dict['user_name'][0]
    user_id = req_dict['user_id'][0]
    channel_id = req_dict['channel_id'][0]

    print(req_dict)


    current_game = Game.objects.get(channel_id=channel_id)
    requesting_player = Player.objects.get(slack_id=user_id, game_id=current_game.id)
    current_team_playing = current_game.current_team_playing

    if requesting_player.team_color != current_team_playing:
        payload = {"replace_original": False, "text": "Please wait for the {} team to finish their turn.".format(current_team_playing)}
    elif requesting_player.is_spymaster == False:
        payload = {"replace_original": False, "text": "You aren't the spymaster for your team."}
    else:
        try:
            hint = req_dict['text'][0]
            formatted_hint = hint.split(",")
            word = formatted_hint[0]
            num_guesses = int(formatted_hint[1])

            payload =  {
                    "text": "<@{}>'s hint: *'{}'*, *{}*".format(user_id, word.strip().upper(), num_guesses),
                    "response_type": "in_channel",
                }
        except:
            payload = {"replace_original": False, "text": "Your hint was improperly formatted."}
    print(payload)
    return HttpResponse(json.dumps(payload), content_type='application/json')
