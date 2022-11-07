from django.shortcuts import render

import json
import os

import requests
from django.http import JsonResponse
from django.views import View
from bot.models import Chat

import random

TELEGRAM_URL = "https://api.telegram.org/bot"
TUTORIAL_BOT_TOKEN = "5641759368:AAHhRsFPUIi9iaRVtmoSeVrYIkochQCmG-8"

# active_game = None
numbers = dict()

# https://api.telegram.org/bot<5641759368:AAHhRsFPUIi9iaRVtmoSeVrYIkochQCmG-8>/setWebhook?url=<url>/webhook/
class BotView(View):
    def post(self, request, *args, **kwargs):
        t_data = json.loads(request.body)
        t_message = t_data["message"]
        t_chat = t_message["chat"]
        is_command = False
        games = ["/number", "/trivia"]
        playing = ["/n", "/t"]

        print("data: ", t_data)

        chat_id = t_chat["id"]

        # chat = Chat.objects.get(ichat_d=chat_id)

        if Chat.objects.filter(chat_id = chat_id).exists():
            print("existo")
        else:
            print("no existo")
            new_chat = Chat(chat_id = chat_id)
            new_chat.save()

        chat = Chat.objects.get(chat_id=chat_id)

        try:
            text = t_message["text"].strip().lower()
        except Exception as e:
            return JsonResponse({"ok": "POST request processed"})


        try:
            entities = t_message["entities"]
            if entities[0]["type"] == "bot_command":
                is_command = True
            print("ent: ", is_command)
        except KeyError:
            print("no hay entities")

        if is_command:
            # procesar comando 
            command = t_message["text"].split()[0]
            command_args = t_message["text"].split()[1:]
            print(command, command_args)

            if chat.active_game != "None":
                if command in games:
                    self.send_message("A game is already active.", chat_id)
                elif command == "/n":
                    try:
                        user_message = int(command_args[0])
                        if user_message > numbers[t_chat["id"]]:
                            self.send_message(f'{t_message["from"]["first_name"]} {t_message["from"]["last_name"]} your number ( {t_message["text"].split()[1]} ) is greater than mine', t_chat["id"])
                        elif user_message < numbers[t_chat["id"]]:
                            self.send_message(f'{t_message["from"]["first_name"]} {t_message["from"]["last_name"]} your number ( {t_message["text"].split()[1]} ) is smaller than mine', t_chat["id"])
                        else:
                            self.send_message(f'{t_message["from"]["first_name"]} {t_message["from"]["last_name"]} yep, that\'s the right number ( {t_message["text"].split()[1]} )', t_chat["id"])
                            del numbers[chat_id]
                            chat.active_game = "None"
                            chat.save()
                    except ValueError:
                        self.send_message("you must enter an integer", t_chat["id"])
                    except KeyError:
                        self.send_message("There's no number to guess! say /number to start", t_chat["id"])
                    except IndexError:
                        self.send_message(f'{t_message["from"]["first_name"]} {t_message["from"]["last_name"]}, you must send a number', t_chat["id"])
                else:
                    self.send_message("idk", t_chat["id"])
            
            else:
                if command == "/number":
                    try:
                        numbers[t_chat["id"]] = random.randint(0, int(command_args[0]))
                        chat.active_game = "number"
                        chat.save()
                        self.send_message(" Number game started, guess the number!", t_chat["id"])
                        print(numbers)
                    except IndexError:
                        self.send_message("Missing game configuration", t_chat["id"])
            

        else:
            self.send_message("I don´t understand", t_chat["id"])
        
        
        




        # text = text.lstrip("/")
        # chat = tb_tutorial_collection.find_one({"chat_id": t_chat["id"]})
        # if not chat:
        #     chat = {
        #         "chat_id": t_chat["id"],
        #         "counter": 0
        #     }
        #     response = tb_tutorial_collection.insert_one(chat)
        #     # we want chat obj to be the same as fetched from collection
        #     chat["_id"] = response.inserted_id

        # if text == "+":
        #     chat["counter"] += 1
        #     tb_tutorial_collection.save(chat)
        #     msg = f"Number of '+' messages that were parsed: {chat['counter']}"
        #     self.send_message(msg, t_chat["id"])
        # elif text == "restart":
        #     blank_data = {"counter": 0}
        #     chat.update(blank_data)
        #     tb_tutorial_collection.save(chat)
        #     msg = "The Tutorial bot was restarted"
        #     self.send_message(msg, t_chat["id"])
        # else:
        #     msg = "Unknown command"
        #     self.send_message(msg, t_chat["id"])

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
        return JsonResponse({"ok": "GET request processed"})
