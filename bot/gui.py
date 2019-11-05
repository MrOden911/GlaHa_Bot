import tkinter as tk
import os
from pprint import pprint
from random import choice
from string import ascii_letters
from threading import Thread, enumerate
from tkinter import ttk
from datetime import datetime as dt
from time import sleep
import sqlite3 as sql

import vk_api as vk
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType


# Декоратор создания нового потока
def new_thread(func):
    def wrapper(*args):
        thread = Thread(target=func,
                        daemon=True,
                        args=args,
                        name="".join(choice(ascii_letters) for i in range(10)))
        thread.start()
        return
    return wrapper


# Декоратор отлова ошибок
def log_error(func):
    def wrapper(*args):
        try:
            func(*args)
        except Exception as exc:
            exc_text = str(dt.now().time()) + '\n' + str(exc) + '\n'
            with open(os.path.join(os.path.realpath('bot'),
                                   'logs\\errors\\{}'.format(dt.now().date())),
                      'a',
                      encoding='utf-8'
                      ) as file:
                try:
                    GlahaBot.print_fastlog('Ой, что-то пошло не так(')
                except Exception as a:
                    exc_ttext = str(dt.now().time()) + '\n' + str(a) + '\n'
                    print(exc_ttext, file=file)
                finally:
                    print(exc_text, file=file)
        return
    return wrapper


class Gui:
    """ОБЩИЙ КЛАСС"""

    def __init__(self):
        # Токен группы VK
        self.__token = 'c9630c65f9b66f4e630558def110623447c8de90840e477bb5ece18f993c7c940c9373ac48eaf681b2349'

        # Подключение SQL
        self.sql_connect = sql.connect(os.path.join(
            os.path.realpath('bot'), 'data\\GodsDB.db'),
            check_same_thread=False
        )

        # Счетчики и словари
        self.list_action = (
            "event_listen",
            "event_read",
            "connect_vk",
        )
        self.active = dict((key, False) for key in self.list_action)
        print(self.active)
        self.counters = {"event": 0,
                         }

        # Настрйока GUI
        self.window_main = tk.Tk()
        self.window_main.title("GlaHa The Bot")
        # Создание вкладок
        tab_control = ttk.Notebook(self.window_main)
        tab_main = tk.Frame(tab_control)
        tab_logs = tk.Frame(tab_control)
        tab_settings = tk.Frame(tab_control)
        tab_data = tk.Frame(tab_control)
        tab_control.add(tab_main, text="Управление")
        tab_control.add(tab_logs, text="Логи")
        tab_control.add(tab_settings, text="Настройки")
        tab_control.add(tab_data, text="База")
        # Создание фреймов на вкладке Управление
        #   Главный фрейм
        lfraim_tab_main = tk.LabelFrame(tab_main, text="Главное меню", font=('Arial', 14))
        lfraim_tab_main.grid(row=1, column=1, sticky='n')
        #       Заголовок
        lable_tab_main = tk.Label(lfraim_tab_main, text="Управление ботом в VK", font=('Papyrus', 13, "bold"))
        lable_tab_main.grid(row=1, column=1, sticky='n')
        #       Фрейм отправки сообщений
        lframe_message = tk.LabelFrame(lfraim_tab_main, text="Сообщение в чат")
        self.text_message = tk.Text(lframe_message, height=2, width=40, font='Arial 14', wrap=tk.WORD)
        button_send_message = tk.Button(lframe_message, text="Отправить")
        lframe_message.grid(row=3, column=1, sticky='n')
        self.text_message.grid(row=2, column=1)
        button_send_message.grid(row=2, column=2)
        #       Фрейм запуска и остановки
        lframe_startstop = tk.LabelFrame(lfraim_tab_main, text="Запуск")
        self.button_start = tk.Button(lframe_startstop, text='Старт', command=self.listen_to_events)
        button_login_vk = tk.Button(lframe_startstop, text='Подключение', command=self.start_bot_vk, bg='#F08080')
        button_stop = tk.Button(lframe_startstop, text='Выключение', command=self.exit)
        lframe_startstop.grid(row=2, column=1, sticky='wn')
        self.button_start.grid(row=2, column=1, padx=2, pady=2)
        button_login_vk.grid(row=1, column=1,  columnspan=2)
        button_stop.grid(row=2, column=2, padx=2, pady=2)
        #       Фрейм статусов
        frame_status = tk.Frame(lfraim_tab_main)
        label_event_listen = tk.Label(frame_status, text='Прослушка', bg="#CD5C5C")
        label_event_read = tk.Label(frame_status, text='Расшифровка', bg="#CD5C5C")
        frame_status.grid(row=4, column=1)
        label_event_listen.grid(row=1, column=1)
        label_event_read.grid(row=1, column=2)

        #   Фрейм отчетов
        lframe_fastlog = tk.LabelFrame(tab_main, text='Лог')
        self.text_fastlog = tk.Text(lframe_fastlog, width=45, height=25, bg="#FAF0E6", wrap=tk.WORD, )
        scroll_fastlog = tk.Scrollbar(lframe_fastlog, command=self.text_fastlog.yview)
        scroll_fastlog.pack(side=tk.RIGHT, fill=tk.Y)
        self.text_fastlog.config(yscrollcommand=scroll_fastlog.set)
        lframe_fastlog.grid(row=1, column=3, rowspan=3)
        self.text_fastlog.pack(side=tk.LEFT)

        tab_control.pack(side=tk.LEFT, fill=tk.Y)

        self.list_labels = {
            'connect_vk': button_login_vk,
            'event_listen': label_event_listen,
            'event_read': label_event_read,
        }
        self.status_changer()
        self.window_main.mainloop()

    @log_error
    def sql_execute(self, comm):
        self.cursor.execute(comm)
        self.sql_connect.commit()

    def login_vk(self):
        session = vk.VkApi(token=self.__token)
        self.long_poll = VkBotLongPoll(session, 169181915)
        self.active['connect_vk'] = True

    @new_thread
    def listen_to_events(self):
        """Получение ивентов от сервера"""
        if self.active['event_listen']:
            self.print_fastlog('Прослушка уже запущена!')
            return
        else:
            self.active['event_listen'] = True
        for event in self.long_poll.listen():
            self.event_reader(event)
        return

    @new_thread
    @log_error
    def event_reader(self, event):
        print(event.type)
        print(event.obj)
        pprint(event)
        if event.type == VkBotEventType.GROUP_JOIN:
            self.sql_add_onjoin(event)
        elif event.type == VkBotEventType.GROUP_LEAVE:
            self.sql_del_onjoin(event)
        return

    def start_bot_vk(self):
        self.login_vk()
        self.print_fastlog('Бот подключен')
        # self.button_start.grid_forget()
        return

    def print_fastlog(self, text):
        self.text_fastlog.insert(tk.END, dt.now().strftime("%H:%M:%S -- ") + text + "\n")
        return

    @new_thread
    def status_changer(self):
        while True:
            for action in self.list_action:
                try:
                    if self.active[action]:
                        self.list_labels[action]['bg'] = '#7FFF00'
                    else:
                        self.list_labels[action]['bg'] = '#F08080'
                except Exception as e:
                    print(e)
            sleep(2)

    def exit(self):
        self.window_main.destroy()
        return

    def sql_generate_table(self):
        cursor = self.sql_connect.cursor()
        cursor.execute("""
        CREATE TABLE onjoin (
        user_id INTEGER NOT NULL UNIQUE,
        god_type TEXT NOT NULL DEFAULT ('usual'),
        PRIMARY KEY(user_id))""")
        self.sql_connect.commit()
        return

    def sql_add_onjoin(self, event):
        cursor = self.sql_connect.cursor()
        cursor.execute("""INSERT INTO onjoin (user_id) VALUES ({0})""".format(int(event.obj.user_id)))
        self.sql_connect.commit()
        self.print_fastlog('Новый Бог!')
        return

    def sql_del_onjoin(self, event):
        cursor = self.sql_connect.cursor()
        cursor.execute("""DELETE FROM onjoin WHERE user_id = {0}""".format(int(event.obj.user_id)))
        self.sql_connect.commit()
        self.print_fastlog('Бог ушел(')
        return


if __name__ == '__main__':
    global GlahaBot
    GlahaBot = Gui()
