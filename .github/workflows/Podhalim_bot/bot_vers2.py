import time
import telebot
import threading
import logging
import mysql.connector
import pandas as pd
import os
import datetime
import json
import sys
import keyword as kwd
import requests
from telebot import types
from random import choice
from tabulate import tabulate
import random

pd.set_option('display.max_rows', None)
pd.set_option('display.width', None)

bot = telebot.TeleBot("7815448347:AAG-9ZnevqUy8L1aHN6DEoh1G3bd_18bAjU")  # Токен бота

# _________________________________________________________________________________

# База данных
CONFIG = {
    'user': 'j1007852',
    'password': 'el|N#2}-F8',
    'host': 'srv201-h-st.jino.ru',
    'database': 'j1007852_13423'
}

# _________________________________________________________________________________

commands = [
    "Можем начать общение заново - /start",
    "Не люблю хвастаться, но я могу много чего. Нажми /help , чтобы узнать ;) ",
    "Хочешь пофлиртовать со мной? - нажми /flirt",
    "Я ещё могу помочь создать персонажа - /generate",
    "/game - угадай имя, которое я придумал для твоего персонажа"
]

flirt = ["Как только увидел тебя, стал заикаться. Думаешь, это надолго?",
         "Твои родичи часом не террористы? А я-то думаю: «Откуда у них такая адская машина?».",
         "Ты – песня, потому что заела в моей голове.",
         "Ты случайно не лягушка-квакушка из болота? Тогда почему меня к тебе так притягивает, как Ивана-царевича.",
         "Прости я тебя не понимаю, – не разговариваю на внеземном.",
         "Я здесь потерял свое сердечко, поможешь найти?",
         "Когда в моей жизни появилась ты, она стала сказкой.",
         "Будь ты конфеткой, я бы тебя съел.",
         "Можно сойти с ума, на Земле сейчас 7, 678, 175, 660 человек, а нужна мне только ты.",
         "Сегодня я услышал звонок, мне сказали, что с небес упал самый красивый ангелочек, это не ты?",
         "Слушай, мне кажется, ты болото, иначе почему меня так затянуло.",
         "Если ты озеро, то я утопленник.",
         "Я вызываю полицию, ты нарушаешь закон о красоте.",
         "Слушай, может поищешь ингалятор, а то у меня перехватило дух после твоего последнего видео.",
         "Давай поставим наши зубные щетки в один стакан.",
         "я не вор, но тебя бы похитил.",
         "Ты гипнотизер, ведь от тебя я потерял голову.",
         "Ты точно энергос, заставляешь биться мое сердце быстрее.",
         "Я стараюсь не моргать, чтобы чаще видеть твой профиль в Тик Ток."]

COLUMN_NAMES_RU = {
    "name": "Имя",
    "strength": "Сила",
    "constitution": "Телосложение",
    "dexterity": "Ловкость",
    "intelligence": "Интеллект",
    "wisdom": "Мудрость",
    "charisma": "Харизма"
}

# _________________________________________________________________________________

# ___Глобальные переменные___
game_started = False
current_name = ""


# _________________________________________________________________________________

# ___Функция для записи данных в базу данных___
def log_command(user_id, username, command):
    conn = None
    try:
        conn = mysql.connector.connect(**CONFIG)
        cursor = conn.cursor()
        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        query = "INSERT INTO logs (user_id, username, command, timestamp) VALUES (%s, %s, %s, %s)"
        cursor.execute(query, (user_id, username, command, current_time))
        conn.commit()
    except mysql.connector.Error as e:
        print(f"Ошибка при записи лога в базу данных: {e}")
    finally:
        if conn:
            cursor.close()
            conn.close()


# ___Функция, извлекающая случайную строку из таблицы БД. Возвращает в виде списка___
def fetch_random_row(table_name):
    conn = None
    try:
        conn = mysql.connector.connect(**CONFIG)
        cursor = conn.cursor()

        cursor.execute(f"SELECT * FROM {table_name} ORDER BY RAND() LIMIT 1")
        row = cursor.fetchone()

        column_names = [description[0] for description in cursor.description]

        return [row], column_names if row else ([], column_names)
    except mysql.connector.Error as e:
        print(f"Произошла ошибка при работе с базой данных: {e}")
        return None, None  # Return None if error occurs

    finally:
        if conn:
            cursor.close()
            conn.close()


# ___Функция возвращает рандомное имя из файла "Names.txt"___
def get_random_name():
    global current_name
    try:
        with open("Names.txt", "r", encoding="utf-8") as file:
            names = [line.strip() for line in file]
    except UnicodeDecodeError:
        try:
            with open("Names.txt", "r", encoding="windows-1251") as file:
                names = [line.strip() for line in file]
        except UnicodeDecodeError:
            try:
                with open("Names.txt", "r", encoding="latin-1") as file:
                    names = [line.strip() for line in file]
            except UnicodeDecodeError:
                return "Ошибка! Не удалось определить кодировку файла. Пожалуйста, сохраните файл в кодировке UTF-8."
    except FileNotFoundError:
        return "Ошибка! Файл с именами не найден. Пожалуйста, создайте файл 'names.txt' и добавьте в него имена."

    if not names:
        return "Ошибка! Файл с именами пуст. Добавьте в него имена."

    current_name = random.choice(names)
    return current_name


# ___Функция для отправки случайного сообщения из файла 'Flirt.txt'___
def send_random_message(chat_id):
    while True:
        try:
            with open('Flirt.txt', "r", encoding="utf-8") as file:
                messages = file.readlines()
            random_message = random.choice(messages).strip()
            bot.send_message(chat_id, random_message)
        except Exception as e:
            print(f"Ошибка при отправке сообщения: {e}")
        time.sleep(600)


# ___Напоминалка___
def send_reminders(chat_id):
    first_rem = "10:00"
    second_rem = "14:00"
    end_rem = "22:08"
    while True:
        now = datetime.datetime.now()
        if now == first_rem or now == second_rem or now == end_rem:
            bot.send_message(chat_id, "И чуть не забыл! Возвращайся скорее... Я скучаю...")
            time.sleep(61)
        time.sleep(1)


# _________________________________________________________________________________


# ___Обработчик команды /generate___
@bot.message_handler(commands=['generate'])
def generate_command(message):
    log_command(message.from_user.id, message.from_user.username, "/generate")
    table_to_fetch = "характеристики"
    data, column_names = fetch_random_row(table_to_fetch)

    if data and data[0]:
        values = data[0][1:]
        column_names_without_id = column_names[1:]

        message_text = ""
        for i, value in enumerate(values):
            column_name_ru = f"{COLUMN_NAMES_RU.get(column_names_without_id[i], column_names_without_id[i])}:"
            message_text += f"{column_name_ru} {value}\n"

        bot.send_message(message.chat.id, message_text)

    else:
        bot.send_message(message.chat.id, "Не удалось извлечь данные из таблицы.")


# ___Обработчик команды /game___
@bot.message_handler(commands=['game'])
def start_game(message):
    log_command(message.from_user.id, message.from_user.username, "/game")
    global game_started, current_name
    game_started = True
    current_name = ""
    bot.reply_to(message, "Дай-ка подумать...")

    try:
        with open("Names.txt", "r", encoding="utf-8") as file:
            names = [line.strip() for line in file]

    except UnicodeDecodeError:
        try:
            with open("Names.txt", "r", encoding="windows-1251") as file:
                names = [line.strip() for line in file]

        except UnicodeDecodeError:
            try:
                with open("Names.txt", "r",
                          encoding="latin-1") as file:  # Если и windows-1251 не сработала попробуйте latin-1
                    names = [line.strip() for line in file]

            except UnicodeDecodeError:
                bot.reply_to(message,
                             "Ошибка! Не удалось определить кодировку файла. Пожалуйста, сохраните файл в кодировке UTF-8.")
                game_started = False
                return

        if not names:
            bot.reply_to(message, "Ошибка! Файл с именами пуст. Добавьте в него имена.")
            game_started = False
            return

        current_name = random.choice(names)
        bot.reply_to(message, "Я загадал имя. Попробуйте угадать! Если устанешь, просто напиши 'мне надоело' ")

    except FileNotFoundError:
        bot.reply_to(message,
                     "Ошибка! Файл с именами не найден. Пожалуйста, создайте файл 'names.txt' и добавьте в него имена.")
        game_started = False


# ___Функция для обработки команды /start___
@bot.message_handler(commands=['start'])
def start(message):
    log_command(message.from_user.id, message.from_user.username, "/start")
    chat_id = message.chat.id
    username = message.from_user.username

    # Случайное приветствие
    random_greeting = "Привет! Ни на что не намекаю, но... " + random.choice(flirt) + " Не хочешь немного пообщаться?"
    bot.send_message(chat_id, random_greeting)


# ___Обработчик команды /flirt___
@bot.message_handler(commands=['flirt'])
def start_message(message):
    log_command(message.from_user.id, message.from_user.username, "/flirt")
    random_flirt = random.choice(flirt)
    bot.reply_to(message, random_flirt)


# ___Обработчик команды /help___
@bot.message_handler(commands=['help'])
def help_message(message):
    log_command(message.from_user.id, message.from_user.username, "/help")
    bot.reply_to(message, "\nДоступные команды:\n" + "\n".join(commands))


# ___Обработчик сообщений___
@bot.message_handler(func=lambda message: game_started)
def guess_name(message):
    global game_started
    user_guess = message.text.strip()

    if user_guess == current_name:
        bot.reply_to(message, f"Поздравляю, Вы угадали! Это имя '{current_name}'.")
        game_started = False
    elif message.text.lower() == "мне надоело":
        game_started = False
        bot.reply_to(message, f"Хорошо, игра окончена. Я загадал {current_name}.")
    else:
        bot.reply_to(message, "Неа")


# ___Обработка всех сообщений___
@bot.message_handler(func=lambda message: True)
def any_message(message):
    if message.text.lower() != "/start" and message.text.lower() != "/generate" and message.text.lower() != "flirt":
        bot.reply_to(message, "\nЗнаешь, я не так уж и безнадёжен:\n" + "\n".join(commands))


# ___Запуск потока для отправки случайных сообщений___
thread = threading.Thread(target=send_random_message, args=(bot.get_updates()[0].message.chat.id,))
thread.start()
bot.polling(none_stop=True)