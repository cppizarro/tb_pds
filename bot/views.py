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


# https://api.telegram.org/bot5641759368:AAHhRsFPUIi9iaRVtmoSeVrYIkochQCmG-8/setWebhook?url=https://project4pds.herokuapp.com/webhook/
# https://api.telegram.org/bot5641759368:AAHhRsFPUIi9iaRVtmoSeVrYIkochQCmG-8/setWebhook?url=https://botapp.loca.lt/webhook/
class BotView(View):
    def post(self, request, *args, **kwargs):
        try:
            t_data = json.loads(request.body)
            t_message = t_data["message"]
            t_chat = t_message["chat"]
            is_command = False
            games = ["/number", "/trivia", "/code"]
            playing = ["/n", "/t", "/c"]

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

            if Member.objects.filter(chat = chat, name = f'{t_message["from"]["first_name"]} {t_message["from"]["last_name"]}').exists():
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
                    
                    elif command == "/n":
                        try:
                            user_message = int(command_args[0])
                            if player.attempts >= chat.attempts_number_game:
                                self.send_message(f'{t_message["from"]["first_name"]} {t_message["from"]["last_name"]} you don´t have more attempts', t_chat["id"])
                                players_ids = list(Member.objects.filter(chat=chat).all().values_list('pk', flat=True))
                                number_of_players = len(players_ids)
                                no_attempts = 0
                                for player_id in players_ids:
                                    player_ = Member.objects.get(pk=player_id)
                                    att = player_.attempts 
                                    if att >= chat.attempts_number_game:
                                        no_attempts += 1
                                if no_attempts == number_of_players:
                                    self.send_message(f'Game finished, no guessed the number: ( {chat.number_number_game} )', t_chat["id"])
                                    chat.active_game = "None"
                                    chat.save()
                                    players_ids = list(Member.objects.filter(chat=chat).all().values_list('pk', flat=True))
                                    for player_id in players_ids:
                                        Member.objects.filter(pk=player_id).update(attempts=0)
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
                                    player.number_games_won += 1
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

                    elif command == "/c":
                        # TODO: procesar respuesta
                        pass

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
                                players_ids = list(Member.objects.filter(chat=chat).all().values_list('pk', flat=True))
                                players = {}
                                for player_id in players_ids:
                                    player_ = Member.objects.get(pk=player_id)
                                    player_.trivia_points = 0
                                    player_.answered_trivia = False
                                    player_.save()
                                limit = int(command_args[1])
                                chat.trivia_mode = mode
                                api_url = 'https://the-trivia-api.com/api/questions?limit={}'.format(limit)
                                response = requests.get(api_url)
                                if response.status_code == requests.codes.ok:
                                    json_questions = json.loads(response.text)
                                    chat.trivia_number_of_questions = limit
                                    chat.trivia_questions = json_questions
                                    chat.active_game = "trivia"
                                    self.send_message("Trivia game started!", t_chat["id"])   
                                    question_number = chat.actual_question_number
                                    question = chat.trivia_questions[question_number]["question"]
                                    correct_answer = chat.trivia_questions[question_number]["correctAnswer"]
                                    chat.tivia_correct_answer = correct_answer
                                    alternatives = chat.trivia_questions[question_number]["incorrectAnswers"]
                                    alternatives.append(correct_answer)
                                    random.shuffle(alternatives)
                                    chat.actual_question_number = 0
                                    chat.trivia_actual_alternatives = alternatives
                                    chat.save()
                                    self.tel_send_inlinebutton(t_chat["id"], question, alternatives)
                                else:
                                    print("Error:", response.status_code, response.text)
                                    return JsonResponse({"ok": "POST request processed"})
                            else:
                                self.send_message("Nonexistent mode", t_chat["id"])
                        except IndexError:
                            self.send_message("Missing game configuration", t_chat["id"])
                        except ValueError:
                            self.send_message("Last configuration must be a number", t_chat["id"])

                    elif command == "/code":
                        # FIXME: hacer que el estandar puedan ser != numeros y no solo 4
                        try:
                            attempts = int(command_args[0])
                            chat.active_game = "code"
                            chat.attempts_code_game = attempts
                            in_code = []
                            code = str()
                            while len(in_code) < 4:
                                digit = str(random.randint(1,9))
                                if digit not in in_code:
                                    in_code.append(digit)
                                    code += digit

                            chat.code = code
                            chat.save()
                            print(code)
                        except IndexError:
                            self.send_message("Missing game configuration", t_chat["id"])
                        except ValueError:
                            self.send_message("Configurations must be numbers", t_chat["id"])

                    else:
                        if command in playing:
                            self.send_message("There is no game active", t_chat["id"])
                        else:
                            self.send_message("Unrecognized command 1", t_chat["id"])
                

            else:
                message = t_message["text"].split()
                print(message)
                if chat.active_game == "trivia":
                    if message[0] == "A)" or message[0] == "B)" or message[0] == "C)" or message[0] == "D)":
                        if chat.trivia_mode == "first":
                            change_question = False
                            if player.answered_trivia == False:
                                player.answered_trivia = True
                                player.save()
                                message.pop(0)
                                answer = ' '.join(message)
                                print(answer)
                                print(chat.tivia_correct_answer)
                                if answer == chat.tivia_correct_answer:
                                    self.send_message(f'{t_message["from"]["first_name"]} {t_message["from"]["last_name"]}, that is the correct answer!', t_chat["id"])
                                    player.trivia_points += 1
                                    player.save()
                                    change_question = True
                                else:
                                    alt_string = chat.trivia_last_alternatives.replace("'","")
                                    alt_string = alt_string.replace("[","")
                                    alt_string = alt_string.replace("]","")
                                    alt_string = alt_string.replace(" ", "")
                                    print("string: ", alt_string)
                                    last_alternatives = alt_string.split(',')
                                    print(last_alternatives)
                                    if answer in last_alternatives:
                                        player.answered_trivia = False
                                        player.save()
                                        self.send_message("pregunta anterior", t_chat["id"])
                                        return JsonResponse({"ok": "POST request processed"})
                                    self.send_message(f'{t_message["from"]["first_name"]} {t_message["from"]["last_name"]}, incorrect answer', t_chat["id"])
                                    players_ids = list(Member.objects.filter(chat=chat).all().values_list('pk', flat=True))
                                    number_of_players = len(players_ids)
                                    already_answered = 0
                                    for player_id in players_ids:
                                        player_ = Member.objects.get(pk=player_id)
                                        answered = player_.answered_trivia 
                                        if answered == True:
                                            already_answered += 1
                                    if already_answered == number_of_players:
                                        change_question = True
                                        self.send_message(f'No one guessed the question: ( {chat.tivia_correct_answer} )', t_chat["id"])

                                if change_question == True:
                                    chat.actual_question_number += 1
                                    chat.save()
                                    print(chat.actual_question_number)
                                    if chat.actual_question_number  == chat.trivia_number_of_questions:
                                        chat.active_game = "None"
                                        chat.actual_question_number = 0
                                        chat.save()                                      
                                        players_ids = list(Member.objects.filter(chat=chat).all().values_list('pk', flat=True))
                                        players = {}
                                        id_and_name = {}
                                        for player_id in players_ids:
                                            player_ = Member.objects.get(pk=player_id)
                                            players[player_.name] = player_.trivia_points
                                            id_and_name[player_.name] = player_id
                                        players = {k: v for k, v in sorted(players.items(), key=lambda item: item[1])}
                                        players =dict(reversed(list(players.items())))
                                        points = list(players.values())
                                        if len(set(points)) == 1:
                                            if points[0] == 0:
                                                return JsonResponse({"ok": "POST request processed"})
                                            else: # todos tuvieron el mismo puntaje 
                                                return JsonResponse({"ok": "POST request processed"})

                                        else:
                                            keys = list(players.keys())
                                            winner_points = players[keys[0]]
                                            winners_key = []
                                            for key in keys:
                                                if players[key] == winner_points:
                                                    winners_key.append(key)

                                            for key in winners_key:
                                                winner_id = id_and_name[key]
                                                winner = Member.objects.get(pk=winner_id)
                                                winner.trivia_games_won += 1
                                                winner.games_won += 1
                                                winner.save()

                                        trivia_points_string = str()
                                        pos = 1
                                        for key, value in players.items():
                                            trivia_points_string += f'{pos}. {key} -> {value}\n'
                                            pos += 1
                                        trivia_points_string = trivia_points_string.rstrip("\n")
                                        end_message = (f'Trivia game finished:\n {trivia_points_string}')
                                        self.send_message(end_message, t_chat["id"])
                                    else:
                                        players_ids = list(Member.objects.filter(chat=chat).all().values_list('pk', flat=True))
                                        for player_id in players_ids:
                                            player_ = Member.objects.get(pk=player_id)
                                            player_.answered_trivia = False
                                            player_.save()
                                        question_number = chat.actual_question_number
                                        question = chat.trivia_questions[question_number]["question"]
                                        correct_answer = chat.trivia_questions[question_number]["correctAnswer"]
                                        chat.tivia_correct_answer = correct_answer
                                        alternatives = chat.trivia_questions[question_number]["incorrectAnswers"]
                                        alternatives.append(correct_answer)
                                        random.shuffle(alternatives)
                                        chat.trivia_last_alternatives = chat.trivia_actual_alternatives
                                        chat.trivia_actual_alternatives = alternatives
                                        chat.save()
                                        print(correct_answer)
                                        self.tel_send_inlinebutton(t_chat["id"], question, alternatives)

                            else:
                                message.pop(0)
                                answer = ' '.join(message)
                                alt_string = chat.trivia_last_alternatives.replace("'","")
                                alt_string = alt_string.replace("[","")
                                alt_string = alt_string.replace("]","")
                                alt_string = alt_string.replace(" ", "")
                                print("string: ", alt_string)
                                last_alternatives = alt_string.split(',')
                                print(last_alternatives)
                                if answer in last_alternatives:
                                    player.answered_trivia = False
                                    player.save()
                                    self.send_message(f'{t_message["from"]["first_name"]} {t_message["from"]["last_name"]}, answer the question again, it changed!', t_chat["id"])
                                    return JsonResponse({"ok": "POST request processed"})
                                self.send_message("You've already answered the question", t_chat["id"])
                                
                                    

                        elif chat.trivia_mode == "time":
                            #TODO: trivia time mode
                            pass
                    else:
                        print("nada")
                else:
                    if message[0] == "A)" or message[0] == "B)" or message[0] == "C)" or message[0] == "D)":
                        self.send_message("There is no trivia game active", t_chat["id"])
                    else:
                        if "Hola" in message:
                            self.send_message(f'Hello {t_message["from"]["first_name"]} {t_message["from"]["last_name"]}!', t_chat["id"])
                        else:
                            return JsonResponse({"ok": "POST request processed"})
                return JsonResponse({"ok": "POST request processed"})
        
        except KeyError:
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

    @staticmethod
    def tel_send_inlinebutton(chat_id, question, alternatives):
        payload = {
            'chat_id': chat_id,
            'text': f'{question}',
            'reply_markup': {
                "resize_keyboard": True,
                "keyboard": [
                    [f'A) {alternatives[0]}'],
                    [f'B) {alternatives[1]}'],
                    [f'C) {alternatives[2]}'],
                    [f'D) {alternatives[3]}']
                ]
            }
        }
        r = requests.post(f"{TELEGRAM_URL}{TUTORIAL_BOT_TOKEN}/sendMessage", json=payload)


    def get(self, request):
        all_chats_id = list(Chat.objects.all().values_list('pk', flat=True))
        global_stats = []
        for id in all_chats_id:
            chat = Chat.objects.get(pk = id)
            players_ids = list(Member.objects.filter(chat=chat).all().values_list('pk', flat=True))
            players = {}
            number_game = {}
            trivia_game = {}
            # hangman_game = {}
            for player_id in players_ids:
                player_ = Member.objects.get(pk=player_id)
                players[player_.name] = player_.games_won
                number_game[player_.name] = player_.number_games_won
                trivia_game[player_.name] = player_.trivia_games_won

            players = {k: v for k, v in sorted(players.items(), key=lambda item: item[1])}
            players =dict(reversed(list(players.items())))
            stats_dict = {}
            pos = 1
            for key, value in players.items():
                stats_dict[f'{pos}) {key}'] = value
                pos += 1

            number_game = {k: v for k, v in sorted(number_game.items(), key=lambda item: item[1])}
            number_game =dict(reversed(list(number_game.items())))
            number_stats_dict = {}
            pos = 1
            for key, value in number_game.items():
                number_stats_dict[f'{pos}) {key}'] = value
                pos += 1

            trivia_game = {k: v for k, v in sorted(trivia_game.items(), key=lambda item: item[1])}
            trivia_game =dict(reversed(list(trivia_game.items())))
            trivia_stats_dict = {}
            pos = 1
            for key, value in trivia_game.items():
                trivia_stats_dict[f'{pos}) {key}'] = value
                pos += 1

            global_stats.append({"chat_name":chat.chat_name, "stats":stats_dict, "number_stats":number_stats_dict, "trivia_stats":trivia_stats_dict})

        context = {
            'stats':global_stats
        }
        return render(request, 'stats.html', context)


def GroupStats(request, group_id):
    chat = Chat.objects.get(pk = group_id)
    players_ids = list(Member.objects.filter(chat=chat).all().values_list('pk', flat=True))
    stats = []
    players = {}
    number_game = {}
    trivia_game = {}
    # hangman_game = {}
    for player_id in players_ids:
        player_ = Member.objects.get(pk=player_id)
        players[player_.name] = player_.games_won
        number_game[player_.name] = player_.number_games_won
        trivia_game[player_.name] = player_.trivia_games_won

    players = {k: v for k, v in sorted(players.items(), key=lambda item: item[1])}
    players =dict(reversed(list(players.items())))
    stats_dict = {}
    pos = 1
    for key, value in players.items():
        stats_dict[f'{pos}) {key}'] = value
        pos += 1

    number_game = {k: v for k, v in sorted(number_game.items(), key=lambda item: item[1])}
    number_game =dict(reversed(list(number_game.items())))
    number_stats_dict = {}
    pos = 1
    for key, value in number_game.items():
        number_stats_dict[f'{pos}) {key}'] = value
        pos += 1

    trivia_game = {k: v for k, v in sorted(trivia_game.items(), key=lambda item: item[1])}
    trivia_game =dict(reversed(list(trivia_game.items())))
    trivia_stats_dict = {}
    pos = 1
    for key, value in trivia_game.items():
        trivia_stats_dict[f'{pos}) {key}'] = value
        pos += 1

    stats.append({"stats":stats_dict, "number_stats":number_stats_dict, "trivia_stats":trivia_stats_dict})

    context ={
        'chat_name': chat.chat_name,
        'group_stats': stats
    }
    return render(request, 'group.html', context)


def Home(request):
    all_chats_id = list(Chat.objects.all().values_list('pk', flat=True))
    print(all_chats_id)
    chats = []
    for id in all_chats_id:
        chat = Chat.objects.get(pk = id)
        group = {"name":chat.chat_name, "id":id}
        chats.append(group)

    print(chats)
    context = {
        'chats': chats
    }
    return render(request, 'home.html', context)



# FIXME: cuando alguien responde despues de la respuesta correcta a veces cuenta como que respondio la siguiente pregunta


# https://api.telegram.org/bot5641759368:AAHhRsFPUIi9iaRVtmoSeVrYIkochQCmG-8/setWebhook?url=https://botapp.loca.lt/webhook/
# lt --port 8000 --subdomain botapp
