from django.shortcuts import render

import json
import os

import requests
from django.http import JsonResponse
from django.views import View
from bot.models import Chat, Member

import random

TELEGRAM_URL = "https://api.telegram.org/bot"
TUTORIAL_BOT_TOKEN = "5641759368:AAHhRsFPUIi9iaRVtmoSeVrYIkochQCmG-8"

# numbers = dict()

# https://api.telegram.org/bot5641759368:AAHhRsFPUIi9iaRVtmoSeVrYIkochQCmG-8/setWebhook?url=https://f990-2800-300-8241-81a0-00-4.sa.ngrok.io/webhook/
# https://api.telegram.org/bot5641759368:AAHhRsFPUIi9iaRVtmoSeVrYIkochQCmG-8/setWebhook?url=https://project4pds.herokuapp.com/webhook/
class BotView(View):
    def post(self, request, *args, **kwargs):
        try:
            t_data = json.loads(request.body)
            t_message = t_data["message"]
            t_chat = t_message["chat"]
            is_command = False
            games = ["/number", "/trivia"]
            playing = ["/n", "/t"]

            print("data: ", t_data)

            chat_id = t_chat["id"]

            if Chat.objects.filter(chat_id = chat_id).exists():
                print("existo")
            else:
                print("no existo")
                if t_chat["type"] == "group":
                    new_chat = Chat(chat_id = chat_id, chat_name = t_chat["title"])
                else:
                    new_chat = Chat(chat_id = chat_id, chat_name = f'{t_message["from"]["first_name"]} {t_message["from"]["last_name"]}')
                new_chat.save()

            chat = Chat.objects.get(chat_id=chat_id)

            if Member.objects.filter(chat = chat).exists() and Member.objects.filter(name = f'{t_message["from"]["first_name"]} {t_message["from"]["last_name"]}').exists():
                print("existo")
            else:
                print("no existo")
                new_member = Member(chat = chat, name = f'{t_message["from"]["first_name"]} {t_message["from"]["last_name"]}')
                new_member.save()

            player = Member.objects.get(chat =chat, name=f'{t_message["from"]["first_name"]} {t_message["from"]["last_name"]}')


            try:
                entities = t_message["entities"]
                if entities[0]["type"] == "bot_command":
                    is_command = True
            except KeyError:
                print("no hay entities")

            if is_command:
                # procesar comando 
                command = t_message["text"].split()[0]
                command_args = t_message["text"].split()[1:]
                print(command, command_args)

                if command == "/help":
                    self.send_message("Available Commands :- \n /number - To play guess the number game\n /n - To send number when number game is active \n /stats - To see statistics\n", t_chat["id"])

                elif chat.active_game != "None":
                    if command in games:
                        self.send_message("A game is already active.", chat_id)
                    elif command == "/n":
                        try:
                            user_message = int(command_args[0])
                            if player.attempts >= chat.attempts_number_game:
                                self.send_message(f'{t_message["from"]["first_name"]} {t_message["from"]["last_name"]} you don´t have more attempts', t_chat["id"])
                                # implementar fin del juego una vez que a todos se les acaban los intentos
                            else:
                                if user_message > chat.number_number_game:
                                    self.send_message(f'{t_message["from"]["first_name"]} {t_message["from"]["last_name"]} your number ( {t_message["text"].split()[1]} ) is greater than mine', t_chat["id"])
                                    player.attempts += 1
                                    player.save()
                                elif user_message < chat.number_number_game:
                                    self.send_message(f'{t_message["from"]["first_name"]} {t_message["from"]["last_name"]} your number ( {t_message["text"].split()[1]} ) is smaller than mine', t_chat["id"])
                                    player.attempts += 1
                                    player.save()
                                else:
                                    self.send_message(f'{t_message["from"]["first_name"]} {t_message["from"]["last_name"]} yep, that\'s the right number ( {t_message["text"].split()[1]} )', t_chat["id"])
                                    chat.active_game = "None"
                                    chat.save()
                                    player.games_won += 1
                                    player.save()
                                    players_ids = list(Member.objects.filter(chat=chat).all().values_list('pk', flat=True))
                                    for player_id in players_ids:
                                        Member.objects.filter(pk=player_id).update(attempts=0)        
                            
                        except ValueError:
                            self.send_message(f'{t_message["from"]["first_name"]} {t_message["from"]["last_name"]}, you must enter an integer', t_chat["id"])
                        except KeyError:
                            self.send_message("There's no number to guess! say /number to start", t_chat["id"])
                        except IndexError:
                            self.send_message(f'{t_message["from"]["first_name"]} {t_message["from"]["last_name"]}, you must send a number', t_chat["id"])

                    elif command == "/t":
                        if chat.trivia_mode == "first":
                            print(chat.trivia_questions[0])
                        elif chat.trivia_mode == "time":
                            return JsonResponse({"ok": "POST request processed"})

                    elif command == "/stop":
                        chat.active_game = "None"
                        chat.save()
                        players_ids = list(Member.objects.filter(chat=chat).all().values_list('pk', flat=True))
                        for player_id in players_ids:
                            Member.objects.filter(pk=player_id).update(attempts=0)
                        self.send_message("Now there is no game active", t_chat["id"])
                        return JsonResponse({"ok": "POST request processed"})
                    elif command == "/stats":
                        self.send_message("There is a game in progress. Please ask for stats when the game is finished", chat_id)
                    else:
                        self.send_message("Unrecognized command", t_chat["id"])
                
                else:
                    if command == "/stats":
                        players_ids = list(Member.objects.filter(chat=chat).all().values_list('pk', flat=True))
                        players = {}
                        for player_id in players_ids:
                            player_ = Member.objects.get(pk=player_id)
                            players[player_.name] = player_.games_won
                        players = {k: v for k, v in sorted(players.items(), key=lambda item: item[1])}
                        players =dict(reversed(list(players.items())))
                        stats_string = str()
                        pos = 1
                        for key, value in players.items():
                            stats_string += f'{pos}. {key} -> {value}\n'
                            pos += 1
                        stats_string = stats_string.rstrip("\n")
                        self.send_message(stats_string, t_chat["id"])
                    elif command == "/stop":
                        self.send_message("There is no game active.", chat_id)
                    elif command == "/number":
                        try:
                            # numbers[t_chat["id"]] = random.randint(0, int(command_args[0]))
                            attempts = int(command_args[1])
                            chat.active_game = "number"
                            chat.attempts_number_game = attempts
                            chat.number_number_game = random.randint(0, int(command_args[0]))
                            chat.save()
                            self.send_message(" Number game started, guess the number!", t_chat["id"])
                        except IndexError:
                            self.send_message("Missing game configuration", t_chat["id"])
                        except ValueError:
                            self.send_message("Configurations must be numbers", t_chat["id"])
                    elif command == "/trivia":
                        try:
                            mode = command_args[0]
                            if mode == "first" or mode == "time": 
                                limit = int(command_args[1])
                                chat.trivia_mode = mode
                                api_url = 'https://the-trivia-api.com/api/questions?limit={}'.format(limit)
                                response = requests.get(api_url)
                                if response.status_code == requests.codes.ok:
                                    json_questions = json.loads(response.text)
                                    chat.trivia_number_of_questions = limit
                                    chat.trivia_questions = json_questions
                                    chat.active_game = "trivia"
                                    chat.save()
                                    self.send_message("Trivia game started!", t_chat["id"])
                                else:
                                    print("Error:", response.status_code, response.text)
                                    return JsonResponse({"ok": "POST request processed"})
                            else:
                                self.send_message("Nonexistent mode", t_chat["id"])
                        except IndexError:
                            self.send_message("Missing game configuration", t_chat["id"])
                        except ValueError:
                            self.send_message("Last configuration must be a number", t_chat["id"])

                    else:
                        if command in playing:
                            self.send_message("There is no game active", t_chat["id"])
                        else:
                            self.send_message("Unrecognized command", t_chat["id"])
                

            else:
                # self.send_message("I don´t understand", t_chat["id"])
                return JsonResponse({"ok": "POST request processed"})
        
        except KeyError:
            print(KeyError)
            return JsonResponse({"ok": "POST request processed"})
        except (ConnectionAbortedError, ConnectionError):
            return JsonResponse({"ok": "POST request processed"})
        

        return JsonResponse({"ok": "POST request processed"})

    @staticmethod
    def send_message(message, chat_id):
        data = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "Markdown",
        }
        
        response = requests.post(
            f"{TELEGRAM_URL}{TUTORIAL_BOT_TOKEN}/sendMessage", data=data
        )


    def get(self, request):
        all_chats_id = list(Chat.objects.all().values_list('pk', flat=True))
        stats = []
        for id in all_chats_id:
            chat = Chat.objects.get(pk = id)
            players_ids = list(Member.objects.filter(chat=chat).all().values_list('pk', flat=True))
            players = {}
            for player_id in players_ids:
                player_ = Member.objects.get(pk=player_id)
                players[player_.name] = player_.games_won
            players = {k: v for k, v in sorted(players.items(), key=lambda item: item[1])}
            players =dict(reversed(list(players.items())))
            stats_string = str()
            pos = 1
            for key, value in players.items():
                stats_string += f'{pos}. {key} -> {value}\n'
                pos += 1
            stats_string = stats_string.rstrip("\n")
            stats_dict = {}
            pos = 1
            for key, value in players.items():
                stats_dict[f'{pos}) {key}'] = value
                pos += 1

            stats.append({"chat_name":chat.chat_name, "stats":stats_dict})

        context = {
            'stats':stats
        }
        return render(request, 'stats.html', context)
        # return JsonResponse({"ok": "GET request processed"})

def Home(request):
    return render(request, 'home.html')
