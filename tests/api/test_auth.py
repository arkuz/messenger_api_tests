import pytest
import os

from helpers.api import API
from helpers.readers import read_yaml
import helpers.const as const
import helpers.tools as tools
import helpers.auth as auth


class TestsAuth:

    config = read_yaml(os.path.join(const.PROJECT, 'config.yaml'))
    user = config['users']['user1']
    url = ''
    api = API

    def setup_method(self):
        self.url = self.config['api']['url']
        phone = self.user['phone']
        code = self.user['code']
        auth_cookies = auth.login_with_cookies(self.url, phone, code)
        self.api = API(self.url, auth_cookies, is_token_auth=False)

    def teardown_method(self):
        auth.logout(self.url)

    '''    
    Пример для авторизации через токен
    def setup_class(self):
        self.url = self.config['api']['url']
        user = self.config['users']['user1']
        data = {
            'phone': user['phone'],
            'code': user['code'],
            'device_id': user['device_id'],
            'type': user['type']
        }
        token = auth.login_with_token(self.url, data)
        self.api = API(self.url, token)
    '''

    @pytest.mark.positive
    @pytest.mark.parametrize("phone, expected", [
        ('+79011111111', '+79011111111'),
        ('+7(901)1111111', '+79011111111'),
        ('+7 901 111 11 11', '+79011111111'),
        ('+7 (901) 111 11-11', '+79011111111'),
        ('7(901) 111 11-11', '+79011111111'),
        ('8 901111 11-11', '+79011111111'),
        # ('+994 000 000 00 00', '+9940000000000'), # падают на новом смс сервисе
        # ('+9940000000000', '+9940000000000')
    ])
    def test_sms_login_valid_phone(self, phone, expected):
        resp = self.api.sms_login(phone)
        resp = resp.json()
        assert 'error' not in resp
        assert resp['result']['phone'] == expected


    @pytest.mark.negative
    @pytest.mark.parametrize("phone", [
        ('+7000000000143554'),
        ('+7000'),
        ('+9940000000000444'),
        ('9940000000000')
    ])
    def test_sms_login_invalid_phone(self, phone):
        resp = self.api.sms_login(phone)
        resp = resp.json()
        assert resp['error'] == 'INVALID_DATA'
        assert resp['details']['phone'] == 'Некорректный номер телефона'


    @pytest.mark.positive
    def test_sms_auth_exist_device(self):
        user = self.config['users']['user5']
        self.api.sms_login(user['phone'])
        data = {
            'phone': user['phone'],
            'code': user['code'],
            'device_id': user['device_id'],
            'type': user['type']
        }
        resp = self.api.sms_auth(data)
        resp = resp.json()
        assert tools.is_items_exist_in_list_of_dict(
            resp['result']['me']['devices'],
            'device_id',
            user['device_id']
        )
        assert len(resp['result']['token']) > 0


    @pytest.mark.positive
    def test_sms_auth_new_device(self):
        user = self.config['users']['user5']
        self.api.sms_login(user['phone'])
        device_id = tools.generate_random_string()
        data = {
            'phone': user['phone'],
            'code': user['code'],
            'device_id': device_id,
            'type': 'web'
        }
        resp = self.api.sms_auth(data)
        resp = resp.json()
        assert tools.is_items_exist_in_list_of_dict(
            resp['result']['me']['devices'],
            'device_id',
            device_id
        )
        assert len(resp['result']['token']) > 0


    @pytest.mark.positive
    def test_sms_cookieauth_valid(self):
        user = self.config['users']['user5']
        self.api.sms_login(user['phone'])
        resp = self.api.sms_cookieauth(user['phone'], user['code'])
        res = resp.json()
        assert 'otvauth=' in resp.headers['Set-Cookie']
        assert res['result']['me']['devices']


    @pytest.mark.positive
    def test_cookieauth_logout_post(self):
        user = self.config['users']['user1']
        self.api.sms_login(user['phone'])
        self.api.sms_cookieauth(user['phone'], user['code'])
        resp = self.api.cookieauth_logout_post()
        assert '<!DOCTYPE html>' in resp.text
        assert 'Set-Cookie' not in resp.headers


    @pytest.mark.positive
    def test_cookieauth_logout_get(self):
        user = self.config['users']['user1']
        self.api.sms_login(user['phone'])
        self.api.sms_cookieauth(user['phone'], user['code'])
        resp = self.api.cookieauth_logout_get()
        assert '<!DOCTYPE html>' in resp.text
        assert 'Set-Cookie' not in resp.headers

