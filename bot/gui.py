import tkinter as tk
import os
from pprint import pprint
from random import choice
from string import ascii_letters, ascii_lowercase
from threading import Thread, Lock
from tkinter import ttk
from datetime import datetime as dt
from time import sleep
import sqlite3 as sql
import pandas as pd
import requests as req
import schedule as sch

import vk_api as vk
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.utils import get_random_id


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


# Преобразователь ввода
def message_decode(message):
    eng = '@#$^&~QWERTYUIOP{}ASDFGHJKL:"ZXCVBNM<>?`qwertyuiop[]asdfghjkl;zxcvbnm,./' + "'"
    rus = '"№;:?ЁЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭЯЧСМИТЬБЮ,ёйцукенгшщзхъфывапролджячсмитьбю.' + "э"
    trans_tab = str.maketrans(eng, rus)
    message = message.lower()
    mess_len = len(message)
    counter_eng_word = 0
    for i in message:
        if i in ascii_letters:
            counter_eng_word += 1
    if counter_eng_word > mess_len * 0.5:
        message = message.translate(trans_tab)
    return message


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
        self.cursor = self.sql_connect.cursor()

        # Счетчики и словари
        self.list_action = (
            "event_listen",
            "event_read",
            "connect_vk",
        )
        self.active = dict((key, False) for key in self.list_action)
        print(self.active)
        list_action_by_ids = (
            'registration',
        )
        self.active_ids = dict((key, []) for key in list_action_by_ids)
        self.sql_lock = Lock()
        self.counters = {"event": 0,
                         }
        self.nicknames = []
        self.ignored_ids = set()
        self.df_sql = {}
        self.df_sql_writer()
        self.chat_ids = (
            2000000001,
            2000000002,
            2000000003,
        )
        self.yes = ['+', 'да', 'yes', 'y', 1, '1']
        self.no = ['-', 'нет', 'no', 'n', 0, '0']

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
        button_login_vk.grid(row=1, column=1, columnspan=2)
        button_stop.grid(row=2, column=2, padx=2, pady=2)
        #       Фрейм статусов
        frame_status = tk.Frame(lfraim_tab_main)
        label_event_listen = tk.Label(frame_status, text='Прослушка', bg="#CD5C5C")
        label_event_read = tk.Label(frame_status, text='Расшифровка', bg="#CD5C5C")
        frame_status.grid(row=4, column=1)
        label_event_listen.grid(row=1, column=1)
        label_event_read.grid(row=1, column=2)

        #       Фрейм отчетов
        lframe_fastlog = tk.LabelFrame(tab_main, text='Лог')
        self.text_fastlog = tk.Text(lframe_fastlog, width=45, height=25, bg="#FAF0E6", wrap=tk.WORD, )
        scroll_fastlog = tk.Scrollbar(lframe_fastlog, command=self.text_fastlog.yview)
        scroll_fastlog.pack(side=tk.RIGHT, fill=tk.Y)
        self.text_fastlog.config(yscrollcommand=scroll_fastlog.set)
        lframe_fastlog.grid(row=1, column=3, rowspan=3)
        self.text_fastlog.pack(side=tk.LEFT)

        #   Вкладка настроек
        self.ch_send_message_to_vk = tk.BooleanVar()
        chb_send_message_to_vk = tk.Checkbutton(
            tab_settings,
            text="Отправка лога в ВК",
            onvalue=True,
            offvalue=False,
            variable=self.ch_send_message_to_vk)
        chb_send_message_to_vk.grid()

        #   Вкладка логов
        #       Лог ошибок
        lframe_errorlog = tk.LabelFrame(tab_logs, text='Лог ошибок')
        self.text_errorlog = tk.Text(lframe_errorlog, width=70, height=10, bg="#FAF0E6", wrap=tk.WORD, )
        scroll_errorlog = tk.Scrollbar(lframe_errorlog, command=self.text_errorlog.yview)
        scroll_errorlog.pack(side=tk.RIGHT, fill=tk.Y)
        self.text_errorlog.config(yscrollcommand=scroll_errorlog.set)
        lframe_errorlog.grid(row=1, column=1, sticky=tk.N, padx=5, pady=5)
        self.text_errorlog.pack(side=tk.LEFT)
        #       Лог сообщений
        lframe_income = tk.LabelFrame(tab_logs, text='Сообщения из чатов')
        self.text_income = tk.Text(lframe_income, width=45, height=28, bg="#FAF0E6", wrap=tk.WORD, )
        scroll_income = tk.Scrollbar(lframe_income, command=self.text_income.yview)
        scroll_income.pack(side=tk.RIGHT, fill=tk.Y)
        self.text_income.config(yscrollcommand=scroll_income.set)
        lframe_income.grid(row=1, column=2, rowspan=2, sticky=tk.N, padx=5, pady=5)
        self.text_income.pack(side=tk.LEFT)

        tab_control.pack(side=tk.LEFT, fill=tk.Y)

        self.list_labels = {
            'connect_vk': button_login_vk,
            'event_listen': label_event_listen,
            'event_read': label_event_read,
        }
        # Schedule функции
        sch.every(5).minutes.do(self.all_gods_data_updater)
        sch.every().hour.at(':00').do(self.zpg_warning_start, 2000000002, 2000000001)
        sch.every().hour.at(':04').do(self.zpg_warning_end, 2000000002, 2000000001)
        sch.every().hour.at(':55').do(self.zpg_warning_before, 2000000002, 2000000001)
        self.schedule_starter()

        self.status_changer()
        self.start_bot_vk()
        self.listen_to_events()
        self.window_main.mainloop()

    # БЛОК ДЕКОРАТОРОВ
    def log_error(func):
        """Декоратор обработки ошибки"""

        def wrapper(self, *args, **kwargs):
            try:
                func(self, *args, **kwargs)
            except Exception as exc:
                self.error_writer(exc)
            return

        return wrapper

    def df_sql_update(func):
        def wrapper(self, *args, **kwargs):
            func(self, *args, **kwargs)
            self.df_sql_writer()
            return

        return wrapper

    # БЛОК ФОНОВЫХ ПРОЦЕССОВ

    @new_thread
    def schedule_starter(self):
        while True:
            sch.run_pending()
            sleep(2)

    def error_writer(self, exc, fun=None):
        """Записывает ошибки в логи"""
        if fun:
            self.active[fun] = False
        exc_text = str(dt.now().time()) + '\n' + str(exc) + '\n'
        with open(os.path.join(os.path.realpath('bot'),
                               'logs\\errors\\{}'.format(dt.now().date())),
                  'a',
                  encoding='utf-8'
                  ) as file:
            try:
                self.print_fastlog('Ой, что-то пошло не так(')
                print(exc_text)
                self.print_errorlog(str(exc))
            except Exception as a:
                self.print_errorlog(str(a))
                exc_ttext = str(dt.now().time()) + '\n' + str(a) + '\n'
                print(exc_ttext, file=file)
            finally:
                print(exc_text, file=file)

    def income_writer(self, text, user_id, chat=None):
        script = "select first_name, last_name from onjoin where user_id=?"
        with self.sql_lock:
            if user_id in self.humans:
                name = " ".join(self.cursor.execute(script, (user_id,)).fetchall()[0])
            else:
                name = 'unknown'
            output_message = "{0}{1} ({2})\n{4}{3}\n\n".format(
                dt.now().strftime("%H:%M:%S "),
                name if not chat else self.api.messages.getConversationsById(
                    peer_ids=(chat,),
                    fields=('nickname',)
                )['items'][0]['chat_settings']['title'],
                self.id_to_nicknames[user_id] if user_id in self.id_to_nicknames.keys() else "unknown_god",
                text,
                "--" if not chat else name + ": "
            )
        self.print_incomelog(output_message)
        with open(os.path.join(os.path.realpath('bot'),
                               'logs\\income_messages\\{}'.format(dt.now().date())),
                  'a',
                  encoding='utf-8'
                  ) as file:
            print(output_message, file=file)
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

    def login_vk(self):
        session = vk.VkApi(token=self.__token)
        self.long_poll_bot = VkBotLongPoll(session, 169181915)
        self.active['connect_vk'] = True
        self.api = session.get_api()
        self.print_fastlog("Бот подключен!")
        self.missed_gods()
        return

    def missed_gods(self):
        """Проверка пропущенных во время бездействия богов"""
        current_ids_vk = self.api.groups.getMembers(group_id=169181915)['items']
        with self.sql_lock:
            self.cursor.execute("""SELECT user_id FROM onjoin where active = 1""")
            current_ids_db = [x[0] for x in self.cursor.fetchall()]
        if len(current_ids_db) != len(current_ids_vk):
            difference = list(set(current_ids_vk) ^ set(current_ids_db))
            self.print_fastlog('Найдены несоответствия Богов в базе и группе!')
            if len(current_ids_vk) > len(current_ids_db):
                for i in difference:
                    self.sql_add_onjoin(user_id=i)
            elif len(current_ids_vk) < len(current_ids_db):
                for i in difference:
                    self.sql_del_onjoin(user_id=i)
        return

    def start_bot_vk(self):
        self.login_vk()
        # self.button_start.grid_forget()
        return

    def exit(self):
        self.window_main.destroy()
        return

    # БЛОК ОТРАБОТКИ СОБЫТИЙ

    @new_thread
    @log_error
    def listen_to_events(self):
        """Получение ивентов от сервера"""
        fun = 'event_listen'
        try:
            if self.active[fun]:
                self.print_fastlog('Прослушка уже запущена!')
                return
            else:
                self.active['event_listen'] = True
            for event in self.long_poll_bot.listen():
                self.event_reader(event)
            self.active[fun] = False
        except Exception as exc:
            self.error_writer(exc, fun=fun)
        return

    @new_thread
    def event_reader(self, event):
        print('-------------------------MAIN-----------------------------')
        print(event.type)
        pprint(event)
        print('----------------------------------------------------------')
        if event.type == VkBotEventType.GROUP_JOIN:
            self.sql_add_onjoin(event=event)
        elif event.type == VkBotEventType.GROUP_LEAVE:
            self.sql_del_onjoin(event=event)
        elif event.type == VkBotEventType.MESSAGE_NEW:
            self.message_handler(event)
        elif event.type == VkBotEventType.MESSAGE_ALLOW:
            self.message_allow(event=event)
        elif event.type == VkBotEventType.MESSAGE_DENY:
            self.message_deny(event=event)
        return

    def message_handler(self, event):
        chat_id = None
        user_id = event.obj.from_id
        if event.from_chat:
            # Сообщения из активного чата
            chat_type = True
            chat_id = event.obj.peer_id
            peer_id = chat_id
        else:
            if user_id not in self.can_write:
                self.message_allow(user_id=user_id)
            peer_id = user_id
            chat_type = False
        message_text = message_decode(event.obj.text)
        self.income_writer(message_text, user_id, chat_id)
        if user_id in self.humans and user_id not in self.ignored_ids and (chat_id is None or chat_id in self.chat_ids):
            if (
                    message_text != ''
                    and message_text != '!'
                    and (
                    'глаш' in message_text
                    or 'глах' in message_text or
                    message_text[0] == '!'
            )
            ):
                if 'привет' in message_text:
                    self.send_message(choice(self.ans_hello), peer_id)
                elif 'спасиб' in message_text:
                    self.send_message(choice(self.ans_thanks), peer_id)
                elif 'ночи' in message_text:
                    self.send_message(choice(self.ans_goodnight), peer_id)
                elif (
                        message_text[0] == '!'
                        or 'глаша,' in message_text
                        or 'глаха,' in message_text
                        or ', глаш' in message_text
                        or ', глах' in message_text
                ):
                    if 'регистр' in message_text:
                        if user_id not in self.active_ids['registration']:
                            self.active_ids['registration'].append(user_id)
                            try:
                                if chat_type:
                                    self.send_message('Пойдем-ка поговорим..', peer_id)
                                if 'токен' in message_text:
                                    self.registration_token(user_id)
                                elif 'ник' in message_text or 'имя' in message_text:
                                    self.registration_nickname(user_id)
                                else:
                                    self.registration(user_id)
                            finally:
                                self.active_ids['registration'].remove(user_id)
                        else:
                            self.send_message('Так ты уже регистрируешься о_О', peer_id)
    #                 elif 'идея' in message_text:
    #                     if 'получить' in message_text:
    #                         self.idea_get(id_cur)
    #                     else:
    #                         self.idea_write(message_text, user_id, chat_type)
    #                 elif 'подзем' in message_text or 'подземелье' in message_text:
    #                     initiator_id_podzem = user_id
    #                     if user_id in self.active_gods:
    #                         self.podzem_start()
    #                     else:
    #                         self.send_message_chat('Не зарегистрировался? Вот и сиди без бревна!')
    #                 elif 'помощь' in message_text or 'хелп' in message_text:
    #                     self.helper(id_cur, chat_type)
    #                 elif 'прогноз' in message_text or 'астро' in message_text:
    #                     self.prognoz_start(id_cur, chat_type)
    #                 elif 'кто' in message_text or 'црщ' in message_text:
    #                     pass
    #                 elif 'база' in message_text:
    #                     self.print_base(id_cur, chat_type)
    #                 elif 'отмена' in message_text or 'отмени' in message_text:
    #                     pass
    #                 elif 'зпг' in message_text or 'язп' in message_text:
    #                     if id_cur in self.admin_id:
    #                         if 'вкл' in message_text:
    #                             self.zpg_start()
    #                         elif 'выкл' in message_text:
    #                             self.active_threads['zpg'] = False
    #                         else:
    #                             self.send_message_chat('И что мне с ним делать?')
    #                     else:
    #                         self.send_message_chat('Извини, у тебя прав маловато :3')
    #                 elif 'утра' in message_text or 'утро' in message_text or 'утре' in message_text:
    #                     self.say_utra(id_cur, chat_type)
    #                 elif 'выкл' in message_text:
    #                     if id_cur in self.admin_id:
    #                         if 'тих' in message_text:
    #                             self.exit_bot_silence()
    #                         else:
    #                             self.exit_bot()
    #                 elif chat_type:
    #                     self.send_message_chat(choice(self.ans_unready))
    #                 else:
    #                     self.send_message_person(choice(self.ans_unready), id_cur)
    #         elif 'побед' in message_text and time() - self.podzem_time < 3600 and chat_type:
    #             self.send_message_chat('Оу, вы победили? Какие молодцы :3')
    #             self.podzem_time = 0
    #         elif chat_type and (
    #                 'утра' in message_text or 'утро' in message_text or 'утре' in message_text) and time() - self.utra_time > 3600:
    #             self.send_message_chat(choice(self.ans_utra))
    #             self.utra_time = time()
    #         elif 'я спать' in message_text:
    #             self.say_goodnight(id_cur, chat_type)
    #     elif not chat_type:
    #         if 'привет' in message_text:
    #             if chat_type:
    #                 self.send_message_chat(choice(self.ans_hello))
    #             else:
    #                 self.send_message_person(choice(self.ans_hello), id_cur)
    #         elif 'спасиб' in message_text:
    #             if chat_type:
    #                 self.send_message_chat(choice(self.ans_thanks))
    #             else:
    #                 self.send_message_person(choice(self.ans_thanks), id_cur)
    #         elif 'ночи' in message_text:
    #             self.say_goodnight(id_cur, chat_type)
    #         elif message_text[
    #             0] == '!' or 'глаша,' in message_text or 'глаха,' in message_text or ', глаш' in message_text or ', глах' in message_text:
    #             if 'идея' in message_text:
    #                 if 'получить' in message_text:
    #                     self.idea_get(id_cur)
    #                 else:
    #                     self.idea_write(message_text, id_cur, chat_type)
    #             elif 'подзем' in message_text or 'подземелье' in message_text:
    #                 self.initiator_id_podzem = id_cur
    #                 if chat_type:
    #                     if id_cur in self.players_id:
    #                         self.podzem_start()
    #                     else:
    #                         self.send_message_chat('Не зарегистрировался? Вот и сиди без бревна!')
    #                 else:
    #                     self.send_message_person('Подзем можно запустить только из общего чата.', id_cur)
    #             elif 'помощь' in message_text or 'хелп' in message_text:
    #                 self.helper(id_cur, chat_type)
    #             elif 'прогноз' in message_text or 'астро' in message_text:
    #                 self.prognoz_start(id_cur, chat_type)
    #             elif 'кто' in message_text or 'who' in message_text:
    #                 pass
    #             elif 'база' in message_text:
    #                 self.print_base(id_cur, chat_type)
    #             elif 'отмена' in message_text or 'отмени' in message_text:
    #                 pass
    #             elif 'зпг' in message_text or 'язп' in message_text:
    #                 if id_cur in self.admin_id:
    #                     if 'вкл' in message_text:
    #                         self.zpg_start()
    #                     elif 'выкл' in message_text:
    #                         self.active_threads['zpg'] = False
    #                     else:
    #                         self.send_message_chat('И что мне с ним делать?')
    #                 else:
    #                     self.send_message_chat('Извини, у тебя прав маловато :3')
    #             elif 'утра' in message_text or 'утро' in message_text or 'утре' in message_text:
    #                 self.say_utra(id_cur, chat_type)
    #             elif 'выкл' in message_text:
    #                 if id_cur in self.admin_id:
    #                     if 'тих' in message_text:
    #                         self.exit_bot_silence()
    #                     else:
    #                         self.exit_bot()
    #             elif chat_type:
    #                 self.send_message_chat(choice(self.ans_unready))
    #             else:
    #                 self.send_message_person(choice(self.ans_unready), id_cur)
        else:
            return
        return

    # БЛОК ФУНКЦИЙ

    @df_sql_update
    def message_allow(self, event=None, user_id=None):
        if event:
            user_id = event.obj.user_id
        elif not user_id:
            return
        if user_id in self.humans:
            with self.sql_lock:
                self.cursor.execute('UPDATE onjoin SET can_write=1 WHERE user_id=?', (user_id,))
                self.sql_connect.commit()
        return

    @df_sql_update
    def message_deny(self, event=None, user_id=None):
        if event:
            user_id = event.obj.user_id
        elif not user_id:
            return
        if user_id in self.humans:
            with self.sql_lock:
                self.cursor.execute('UPDATE onjoin SET can_write=0 WHERE user_id=?', (user_id,))
                self.sql_connect.commit()
        return

    @new_thread
    def zpg_warning_start(self, *chat_ids):
        for chat_id in chat_ids:
            self.send_message('ZPG арена открылась!', chat_id)

    @new_thread
    def zpg_warning_end(self, *chat_ids):
        for chat_id in chat_ids:
            self.send_message('ZPG арена закрылась.', chat_id)

    @new_thread
    def zpg_warning_before(self, *chat_ids):
        for chat_id in chat_ids:
            self.send_message('ZPG арена открывается через 5 минут!', chat_id)

    def person_message_handler(self, user_id):
        while True:
            event = self.long_poll_bot.check()
            if not event:
                continue
            else:
                event = event[0]
            if event.type == VkBotEventType.MESSAGE_NEW and not event.from_chat and event.obj.from_id == user_id:
                self.ignored_ids.discard(user_id)
                return event.obj.text
            else:
                continue

    def registration(self, user_id):
        self.ignored_ids.add(user_id)
        self.send_message('Добро пожаловать, Бог.', user_id)
        if user_id in self.id_to_nicknames.keys():
            self.send_message('Упс, кажется ты уже зарегестрирован.\nХотите изменить регистрационные данные?',
                              user_id)
            while True:
                ans = self.person_message_handler(user_id).lower()
                if ans in self.yes:
                    self.send_message(
                        """
                        Выбери изменяемые данные:
                        1 - Никнейм
                        2 - Токен
                        """,
                        user_id)
                    while True:
                        ans = self.person_message_handler(user_id).lower()
                        if ans == '1' or ans.lower() == 'никнейм':
                            self.registration_nickname(user_id)
                            break
                        elif ans == '2' or ans.lower() == 'токен':
                            self.registration_token(user_id)
                            break
                        else:
                            self.send_message('Такого нет в списке(', user_id)
                    break
                elif ans in self.no:
                    self.send_message('На нет и суда нет.', user_id)
        else:
            self.registration_nickname(user_id)
            self.registration_token(user_id)
        return

    @df_sql_update
    def registration_nickname(self, user_id):
        while True:
            c = 0
            god_nickname_1 = ""
            god_nickname_2 = ""
            self.send_message('Поведай же мне имя свое!', user_id)
            while god_nickname_1 in (None, "", 0, "0", "1", 1):
                if c > 0:
                    self.send_message('Как-то слабо верится, введи еще раз..', user_id)
                c += 1
                god_nickname_1 = self.person_message_handler(user_id)
            c = 0
            self.send_message('Повтори еще раз для проверки..', user_id)
            while god_nickname_2 in (None, "", 0, "0", "1", 1):
                if c > 0:
                    self.send_message('Как-то слабо верится, введи еще раз..', user_id)
                c += 1
                god_nickname_2 = self.person_message_handler(user_id)
            if god_nickname_1 != god_nickname_2:
                self.send_message('Упс, кажется ты ошибся, придется повторить..', user_id)
                continue
            elif god_nickname_1 in self.nicknames_to_id.keys():
                self.send_message('Упс, такой ник уже существует!\n Придется повторить..', user_id)
                continue
            else:
                break
        with self.sql_lock:
            if user_id in self.id_to_nicknames.keys():
                self.cursor.execute(
                    f'UPDATE god_data SET god_nickname=? WHERE user_id=?',
                    (god_nickname_1, user_id)

                )
                self.cursor.execute(
                    f'UPDATE god_data SET approve=? WHERE user_id=?',
                    (0, user_id)
                )
                self.sql_connect.commit()
            else:
                self.cursor.execute(f'INSERT INTO god_data(user_id, god_nickname) VALUES (?,?)',
                                    (user_id, god_nickname_1))
                self.sql_connect.commit()
            self.send_message('Никнейм сохранен.', user_id)
        return

    @df_sql_update
    def registration_token(self, user_id):
        if user_id not in self.id_to_nicknames.keys():
            self.send_message('Ты еще не зарегистрировал Никнейм!', user_id)
            return
        self.send_message('Мне нужна твоя одежда, и твой токен!', user_id)
        self.send_message('''
            Шучу, в этот раз мне нужен только токен из Годвилля :3
            Токен -- это уникальный ключ доступа к данным твоего героя из Годвилля.
            С его помощью я смогу чуть более тщательно следить за его передвижениями, и предупреждать тебя о некоторых полезных событиях :3
            Торжественно клянусь, что замышляю только шало... Нет нет нет, все твои данные будут строго защищены, и никто кроме меня их не увидит.
            Иногда твой токен будет обновляться. Поэтому его придется вводить заново!
            
            Для получения токена:
            1) Открой ссылку в браузере
            https://godville.net/user/profile/settings
            2) Сгенерируй новый токен во вкладке "Ключ API", нажми "Применить"
            
            Если ты отказываешься делиться со мной своим токеном, то просто отправь мне сообщение с текстом "None", или любую белиберду.
            Если же ты все таки решился, то напиши мне свой токен.

            ''', user_id, 'photo-169181915_457239017')
        ans = self.person_message_handler(user_id)
        if ans.lower() != 'none':
            for letter in ans:
                if letter not in ascii_lowercase + '0987654321':
                    with self.sql_lock:
                        self.cursor.execute(f'UPDATE functions SET advanced=0 WHERE user_id=?', (user_id,))
                        self.cursor.execute(f'UPDATE god_data SET token=NULL WHERE user_id=?', (user_id,))
                        self.sql_connect.commit()
                    self.send_message('Токен не был записан.', user_id)
                    return
        if ans.lower() == 'none':
            with self.sql_lock:
                self.cursor.execute(f'UPDATE functions SET advanced=0 WHERE user_id=?', (user_id,))
                self.cursor.execute(f'UPDATE god_data SET token=NULL WHERE user_id=?', (user_id,))
                self.sql_connect.commit()
            self.send_message('Токен не был записан.', user_id)
        else:
            with self.sql_lock:
                self.cursor.execute(f'UPDATE functions SET advanced=1 WHERE user_id=?', (user_id,))
                self.cursor.execute(f'UPDATE god_data SET token=? WHERE user_id=?', (ans, user_id))
                self.sql_connect.commit()
            self.send_message('Записала :3', user_id)
        return

    @new_thread
    def all_gods_data_updater(self):
        for god_name in self.nicknames_to_id.keys():
            self.god_data_update(god_name)
            sleep(10)
        return

    @df_sql_update
    def god_data_update(self, god_name):
        user_id = self.nicknames_to_id[god_name]
        with self.sql_lock:
            if not self.cursor.execute(
                    f'SELECT approve FROM god_data WHERE user_id={self.nicknames_to_id[god_name]}').fetchall()[0][0]:
                self.print_fastlog(f'Бог {god_name} не подтвержден, данные не обновлены.')
                return
        if self.nicknames_to_id[god_name] in self.advanced_gods:
            token = self.cursor.execute("SELECT token FROM god_data WHERE god_nickname=?", (god_name,)).fetchall()[0][0]
            print(token)
            if token is not None:
                token = "/" + token
            else:
                token = ""
                self.send_message('Кажется твой токен устарел :(\nЗарегистрируй новый, если хочешь получать всю самую '
                                  'свежую статистику о своем герое!', self.nicknames_to_id[god_name])
                with self.sql_lock:
                    self.cursor.execute(
                        'UPDATE functions SET advanced=0 WHERE user_id=?',
                        (self.nicknames_to_id[god_name],)
                    )
                    self.sql_connect.commit()
        else:
            token = ""
        json_get = req.get(f'https://godville.net/gods/api/{god_name}{token}')
        print(type(json_get))
        pprint(json_get)
        json_get = json_get.json()
        pprint(json_get)
        if 'expired' in json_get.keys():
            self.print_fastlog(f'Данные {god_name} устарели в Годвилле!')
            return
        json_get['update_time'] = dt.now().strftime("%H:%M:%S")
        if 'activatables' in json_get.keys():
            json_get['activatables'] = str(json_get['activatables'])
        try:
            json_get.update(json_get['pet'])
        except:
            pass
        column_list = ['activatables', 'alignment', 'arena_fight', 'arena_lost', 'arena_won', 'ark_completed_at',
                       'ark_f', 'ark_m', 'aura', 'boss_name', 'boss_power', 'bricks_cnt', 'clan', 'clan_position',
                       'diary_last', 'distance', 'exp_progress', 'fight_type', 'gender', 'godpower', 'gold_approx',
                       'health', 'inventory_max_num', 'inventory_num', 'level', 'max_health', 'motto', 'name', 'quest',
                       'quest_progress', 'savings', 'savings_completed_at', 'shop_name', 't_level',
                       'temple_completed_at', 'town_name', 'wood_cnt', 'words', 'pet_class', 'pet_level', 'pet_name',
                       'wounded', 'update_time']
        result_list = []
        for i in column_list:
            if i in json_get.keys():
                result_list.append(json_get[i])
            else:
                result_list.append(None)
        res_column_list = "activatables=?"
        for column in column_list[1:]:
            res_column_list += f", {column}=?"
        with self.sql_lock:
            self.cursor.execute(f'update god_data set {res_column_list} WHERE user_id={self.nicknames_to_id[god_name]}',
                                result_list)
            self.sql_connect.commit()
        if token \
                != '' and 'distance' not in json_get.keys():
            self.send_message('Кажется твой токен устарел :(\nЗарегистрируй новый, если хочешь получать всю самую '
                              'свежую статистику о своем герое!', self.nicknames_to_id[god_name])
            with self.sql_lock:
                self.cursor.execute(
                    'UPDATE functions SET advanced=0 WHERE user_id=?',
                    (self.nicknames_to_id[god_name],)
                )
                self.cursor.execute(f'UPDATE god_data SET token=NULL WHERE user_id={user_id}')
                self.sql_connect.commit()
        return

    def send_message(self, text, peer_id, attachment=''):
        if peer_id < 2000000000 and peer_id not in self.can_write:
            self.print_fastlog(f'Не удалось написать сообщение {peer_id if peer_id not in self.id_to_nicknames else self.id_to_nicknames[peer_id]}\nПользователь не дал доступ к сообщениям!')
            return
        self.api.messages.send(peer_id=peer_id, message=text, random_id=get_random_id(), attachment=attachment)
        return

    def df_sql_writer(self):
        with self.sql_lock:
            for table in sum(self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall(), ()):
                self.df_sql[table] = pd.read_sql_query("select * from {0}".format(table), self.sql_connect)
        df = self.df_sql['onjoin']

        self.admin_ids = []
        self.humans = []
        self.can_write = []
        for i in df[df['god_type'] == "admin"].user_id:
            self.admin_ids.append(i)
        for i in df.user_id:
            self.humans.append(i)
        for i in df[df['can_write'] == 1].user_id:
            self.can_write.append(i)
        for i in self.df_sql.values():
            print(i)

        df = self.df_sql['god_data']
        self.active_gods = []
        self.registered_gods = []
        for i in df.user_id:
            self.registered_gods.append(i)
        for i in df[df['approve'] == 1].user_id:
            self.active_gods.append(i)

        df = self.df_sql['functions']
        self.advanced_gods = []
        for i in df[df['advanced'] == 1].user_id:
            self.advanced_gods.append(i)

        self.id_to_nicknames = {}
        self.nicknames_to_id = {}
        with self.sql_lock:
            for i in self.cursor.execute('SELECT user_id, god_nickname FROM god_data').fetchall():
                self.id_to_nicknames[i[0]] = i[1]
                self.nicknames_to_id[i[1]] = i[0]
        return

    # БЛОК ЗАПИСИ ЛОГОВ
    def print_fastlog(self, text):
        self.text_fastlog.insert(tk.END, dt.now().strftime("%H:%M:%S -- ") + text + "\n")
        if self.ch_send_message_to_vk.get():
            self.api.messages.send(user_id=54228077, message=text, random_id=get_random_id())
        return

    def print_errorlog(self, text):
        self.text_errorlog.insert(tk.END, dt.now().strftime("%H:%M:%S -- ") + text + "\n")
        return

    def print_incomelog(self, output_message):
        self.text_income.insert(
            tk.END,
            output_message
        )
        return

    # БЛОК SQL

    @log_error
    def sql_execute(self, comm):
        self.cursor.execute(comm)
        self.sql_connect.commit()

    def sql_redact_onjoin(self):
        pass

    @df_sql_update
    def sql_add_onjoin(self, user_id=None, event=None):
        if event:
            user_id = int(event.obj.user_id)
        elif not user_id:
            self.print_fastlog('Нет user_id!')
            return
        if type(user_id) != int:
            user_id = int(user_id)
        data = self.api.users.get(user_ids=user_id, fields=['sex', 'first_name', 'last_name'])[0]
        if data['sex'] == 2:
            sex = 'man'
        elif data['sex'] == 1:
            sex = 'woman'
        else:
            sex = None
        with self.sql_lock:
            try:
                self.cursor.execute(
                    """INSERT INTO onjoin (user_id, first_name, last_name, sex, active) VALUES (?,?,?,?,?)""",
                    [user_id,
                     data['first_name'],
                     data['last_name'],
                     sex,
                     1])
                self.cursor.execute("""INSERT INTO functions(user_id) VALUES (?)""", user_id)
            except Exception:
                self.cursor.execute(
                    """
                    update onjoin set 
                    first_name = ?,
                    last_name = ?,
                    sex = ?,
                    'active'= ?
                    where user_id = ?""", (
                        data['first_name'],
                        data['last_name'],
                        sex,
                        True,
                        user_id))
            self.sql_connect.commit()
        self.print_fastlog('Новый Бог!')
        return

    @df_sql_update
    def sql_del_onjoin(self, user_id=None, event=None):
        if event:
            user_id = int(event.obj.user_id)
        elif not user_id:
            self.print_fastlog('Нет user_id!')
            return
        if type(user_id) != int:
            user_id = int(user_id)

        with self.sql_lock:
            self.cursor.execute("""UPDATE onjoin SET active = 0 WHERE user_id = {0}""".format(user_id))
            self.sql_connect.commit()
        self.print_fastlog('Бог ушел(')
        return


if __name__ == '__main__':
    GlahaBot = Gui()
