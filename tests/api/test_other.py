import pytest
import os
import datetime

from helpers.api import API
from helpers.readers import read_json, read_yaml
import helpers.const as const
import helpers.auth as auth


class TestsOther:

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
    def test_ping_post(self):
        resp = self.api.ping_post()
        resp = resp.json()
        assert 'error' not in resp
        assert resp['result'] == 'pong'


    @pytest.mark.positive
    def test_ping_get(self):
        resp = self.api.ping_get()
        resp = resp.json()
        assert 'error' not in resp
        assert resp['result'] == 'pong'


    @pytest.mark.positive
    def test_ping_post_delay_sec(self):
        delay_sec = 2
        time_now = datetime.datetime.now()
        resp = self.api.ping_post(delay_sec)
        time_then = datetime.datetime.now()
        delta_time = time_then - time_now
        resp = resp.json()
        assert 'error' not in resp
        assert resp['result'] == 'pong'
        assert delta_time.seconds >= delay_sec


    @pytest.mark.positive
    def test_ping_get_delay_sec(self):
        delay_sec = 2
        time_now = datetime.datetime.now()
        resp = self.api.ping_get(delay_sec)
        time_then = datetime.datetime.now()
        delta_time = time_then - time_now
        resp = resp.json()
        assert 'error' not in resp
        assert resp['result'] == 'pong'
        assert delta_time.seconds >= delay_sec


    @pytest.mark.positive
    def test_time(self):
        resp = self.api.time()
        local_date = str(datetime.datetime.today())
        resp = resp.json()
        assert 'error' not in resp
        assert local_date[0:10] in resp['result']


    @pytest.mark.positive
    def test_countries(self):
        resp = self.api.countries()
        path = os.path.join(const.EXPECTED_RESULTS, 'countries.json')
        expected = read_json(path)
        resp = resp.json()
        assert 'error' not in resp
        assert resp['result'] == expected['result']

