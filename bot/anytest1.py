import tkinter as tk
import os
from pprint import pprint
from random import choice
from string import ascii_letters
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

# def new_thread(func):
#     def wrapper(*args):
#         thread = Thread(target=func,
#                         daemon=True,
#                         args=args,
#                         name="".join(choice(ascii_letters) for i in range(10)))
#         thread.start()
#         return
#
#     return wrapper
#
# def job(*fk):
#     print('fk')
#     for i in fk:
#         print(i)
# raise ValueError
# sch.every().hour.at('54:20').do(job, 12, 15)
# while True:
#     sch.run_pending()
#     sleep(1)


# print(None)
# pprint(req.get('http://godville.net/gods/api/oden911' + "/f0094ca6e92b").json())

# token = 'c9630c65f9b66f4e630558def110623447c8de90840e477bb5ece18f993c7c940c9373ac48eaf681b2349'
# session = vk.VkApi(token=token)
# api = session.get_api()
# api.messages.send(peer_id=54228077, attachment="", random_id=get_random_id(), message='af')

# sql_connect = sql.connect(os.path.join(
#     os.path.realpath('bot'), 'data\\GodsDB.db'),
#     check_same_thread=False
# )
# cursor = sql_connect.cursor()
#
# print(cursor.execute('SELECT approve FROM god_data').fetchall())
# print(cursor.execute("SELECT token FROM god_data WHERE god_nickname=?", ('Oden911',)).fetchall()[0][0])
# print([i[0] for i in cursor.description])

# print(cursor.fetchall())
# sql_connect.commit()
#
# cursor.execute('''
# CREATE TABLE god_data (
# user_id	INTEGER NOT NULL UNIQUE,
# god_nickname	TEXT NOT NULL UNIQUE,
# token	TEXT DEFAULT NULL UNIQUE,
# PRIMARY KEY(user_id),
# FOREIGN KEY(user_id) REFERENCES onjoin(user_id) ON DELETE CASCADE
# )''')
# pprint(cursor.description)
# pprint(api.messages.getConversationsById(
#                 peer_ids=2000000003,
#                 fields='title'
#             )['items'][0]['chat_settings']['title'])
# sql_connect.commit()
# db = pd.read_sql_query("select * from onjoin", sql_connect)
#
# pprint(cursor.execute("select * from onjoin inner join functions on functions.user_id=onjoin.user_id").fetchall())

