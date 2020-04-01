import os
import json
import random
import string
from datetime import datetime


def get_project_path(path):
    """ Функция возвращает путь до корневой папки проекта """
    proj_name = 'messenger_tests'
    while os.path.split(path)[1] != proj_name:
        path = os.path.split(path)[0]
    return path


def generate_random_string(length=17):
    """ Функция генерирует случайный набор букв """
    name = ''
    for _ in range(1, length):
        name += random.choice(string.ascii_letters)
    return name


def is_items_exist_in_list_of_dict(list, key, value):
    """ Функция принимает на вход список словарей
    и ищет пару key, value перебирая все словари в списке"""
    for el in list:
        for k,v in el.items():
            if k == key and v == value:
                return True
    return False


def print_formatted_json(_json, ensure_ascii=True, indent=2):
    """ Функция печатает отформатированный json. Используется для отладки """
    print(json.dumps(_json, ensure_ascii=ensure_ascii, indent=indent))


def delete_all_teams(api_obj):
    """ Функция удаляет все команды юзера. Используется для отладки
     Возвращает True если все команды удалены """
    resp = api_obj.me().json()
    for item in resp['result']['teams']:
        api_obj.delete_team(item['uid'])
    resp = api_obj.me().json()
    return len(resp['result']['teams']) == 0


def get_datetime_iso_string(dt):
    """
    Функция возвращает строку в формате ISO
    dt типа datetime.datetime
    """
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

