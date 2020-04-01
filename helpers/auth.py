import requests as req

from helpers.api import API


def __sms_login(url, phone):
    """
    endpoint /sms-login методом POST
    Вход по SMS. Отправляем SMS с кодом на телефон.
    """
    data = {'phone': phone}
    endpoint = '/sms-login'
    url += endpoint
    return req.post(url, data)


def __sms_auth(url, data):
    """
    endpoint /sms-auth методом POST
    Авторизация. Вводим код.
    Обязательные поля: code, device_id, phone, type
    В data передаем json
        data = {
            'phone': user['phone'],
            'code': user['code'],
            'device_id': user['device_id'],
            'type': user['type']
        }
    """
    endpoint = '/sms-auth'
    url += endpoint
    return req.post(url, data)


def __sms_cookieauth(url, phone, code):
    """
    endpoint /sms-cookieauth методом POST
    Авторизация. Отличие от просто sms-auth/: не требуется указывать устройство,
    не выдаётся токен, а просто выставляется кука, с которой можно ходить с запросами к API и коннектиться по ws.
    """
    data = {'phone': phone,
            'code': code}
    endpoint = '/sms-cookieauth'
    url += endpoint
    return req.post(url, data)


def __cookieauth_logout_get(url):
    """
    endpoint /cookieauth-logout методом GET
    Выход для /sms-cookieauth
    """
    endpoint = '/cookieauth-logout'
    url += endpoint
    return req.get(url)


def login_with_cookies(url, phone, code):
    """ Логин по куке """
    __sms_login(url, phone)
    resp = __sms_cookieauth(url, phone, code)
    return resp.cookies['otvauth']


def logout(url):
    """ Логаут для login_with_cookies """
    return __cookieauth_logout_get(url)


def login_with_token(url, data):
    """ Логин по токену
        data = {
            'phone': user['phone'],
            'code': user['code'],
            'device_id': user['device_id'],
            'type': user['type']
        } """
    __sms_login(url, data['phone'])
    resp = __sms_auth(url, data)
    return resp.json()['result']['token']


def login_another_user(url, phone, code):
    auth_cookies = login_with_cookies(url, phone, code)
    return API(url, auth_cookies, is_token_auth=False)

