import os, random, json, requests
from django.shortcuts import render
from django.http import HttpResponse

from .models import Greeting, Game, Player

# Create your views here.
def index(request):
    # return HttpResponse('codenames from Python!')
    return render(request, 'index.html')

def db(request):
    greeting = Greeting()
    greeting.save()

    greetings = Greeting.objects.all()

    return render(request, 'db.html', {'greetings': greetings})

def test_webhook(request):
    webhook_url = 'https://hooks.slack.com/services/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'
    payload={
            "text": "Would you like to play a game?",
            "attachments": [
                {
                    "text": "Choose a game to play",
                    "fallback": "You are unable to choose a game",
                    "callback_id": "wopr_game",
                    "color": "#3AA3E3",
                    "attachment_type": "default",
                    "actions": [
                        {
                            "name": "chess",
                            "text": "Chess",
                            "type": "button",
                            "value": "chess"
                        },
                        {
                            "name": "maze",
                            "text": "Falken's Maze",
                            "type": "button",
                            "value": "maze"
                        },
                        {
                            "name": "war",
                            "text": "Thermonuclear War",
                            "style": "danger",
                            "type": "button",
                            "value": "war",
                            "confirm": {
                                "title": "Are you sure?",
                                "text": "Wouldn't you prefer a good game of chess?",
                                "ok_text": "Yes",
                                "dismiss_text": "No"
                            }
                        }
                    ]
                }
            ]
        }

    # headers = {'content-type': 'application/json', 'token': 'xoxp-125493265142-124135210929-126650312950-833a204c78331c4b6f6add0f13a7a6ad'}
    # requests.post(webhook_url, data=json.dumps(payload), headers=headers)
    return HttpResponse(json.dumps(payload), content_type='application/json')

def generate_wordset(request):
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

    data = json.dumps({"words_list": words_list, "map_card": map_card})
    Game.objects.create(
        map_card=json.dumps(map_card),
        word_set=json.dumps(words_list),
        channel_id="0"
    )

    return HttpResponse(data, content_type='application/json')

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
    print(request)
    return HttpResponse(json.dumps({'text': "hello world"}), content_type='application/json')
