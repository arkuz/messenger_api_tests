import pytest
import os
import json

from helpers.api import API
from helpers.readers import read_yaml
import helpers.const as const
import helpers.auth as auth
import helpers.tools as tools
import helpers.functions as func


class TestsTeam:
    config = read_yaml(os.path.join(const.PROJECT, 'config.yaml'))
    user = config['users']['user1']
    phone = config['users']['user1']['phone']
    code = config['users']['user1']['code']

    user2 = config['users']['user2']
    phone2 = config['users']['user2']['phone']
    code2 = config['users']['user2']['code']

    user3 = config['users']['user3']
    phone3 = config['users']['user3']['phone']
    code3 = config['users']['user3']['code']

    user4 = config['users']['user4']
    phone4 = config['users']['user4']['phone']
    code4 = config['users']['user4']['code']
    url = ''
    api = API
    invalid_team_uid = '00000000-0000-0000-0000-982d4bac29a1'


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

    @pytest.mark.negative
    def test_add_team_with_empty_name(self):
        data = {'name': ''}
        resp = self.api.add_team(data)
        resp = resp.json()
        assert const.INVALID_DATA == resp['error']
        assert 'Обязательное поле.' == resp['details']['name']


    @pytest.mark.positive
    def test_add_team_with_name_one_symbol(self):
        name = tools.generate_random_string(2)
        data = {'name': name}
        resp = self.api.add_team(data)
        resp = resp.json()
        assert 'error' not in resp
        assert resp['result']['name'] == name


    @pytest.mark.positive
    def test_add_team_with_name_100_symbols(self):
        name = tools.generate_random_string(101)
        data = {'name': name}
        resp = self.api.add_team(data)
        resp = resp.json()
        assert 'error' not in resp
        assert resp['result']['name'] == name


    @pytest.mark.negative
    def test_add_team_with_name_101_symbols(self):
        data = {'name': tools.generate_random_string(102)}
        resp = self.api.add_team(data)
        resp = resp.json()
        assert const.INVALID_DATA == resp['error']
        assert 'Убедитесь, что это значение содержит не более 100 символов (сейчас 101).' == resp['details']['name']


    @pytest.mark.positive
    @pytest.mark.parametrize("first_symbol", [
        '1','@','#','_ _','а','Я'
    ])
    def test_add_team_with_name_start_with(self, first_symbol):
        name = first_symbol + tools.generate_random_string(30)
        data = {'name': name}
        resp = self.api.add_team(data)
        resp = resp.json()
        assert 'error' not in resp
        assert resp['result']['name'] == name


    @pytest.mark.positive
    def test_add_team_invite_user_without_firstname_and_lastname(self):
        name = tools.generate_random_string()
        phone = self.config['users']['user2']['phone']
        data = {'name': name,
                'contacts': [
                    {'phone': phone}
                ]}
        data_json = json.dumps(data)
        resp = self.api.add_team(data_json).json()
        assert 'error' not in resp
        assert resp['result']['name'] == name
        assert resp['result']['contacts'][0]['contact_phone'] == phone


    @pytest.mark.positive
    def test_get_teams(self):
        resp = self.api.get_teams()
        resp = resp.json()
        assert 'error' not in resp
        for item in resp['result']:
            assert 'name' in item


    @pytest.mark.positive
    @pytest.mark.parametrize("filename", [
        'tiger',
        'TIGER.JPEG',
        'tiger.jpg',
        'tiger.PNG'
    ])
    def test_upload_team_icon_valid(self, filename):
        '''
        Пока доступны только PNG и JPG
        'tiger.bmp',
        'tiger.gif',
        'tiger.tiff'
        '''
        resp = func.add_team(self.api)
        resp = self.api.upload_team_icon(resp['uid'], os.path.join(const.TD_FILES, filename))
        resp = resp.json()
        assert 'error' not in resp
        assert resp['result']['lg']['url']
        assert resp['result']['sm']['url']


    @pytest.mark.negative
    def test_upload_team_icon_member(self):
        team = func.add_team(self.api)
        team_uid = team['uid']
        func.add_contact(self.api, team_uid, self.phone2, role='member')
        api2 = auth.login_another_user(self.url, self.phone2, self.code2)
        resp = api2.upload_team_icon(team_uid, os.path.join(const.TD_FILES, 'tiger.jpg'))
        resp = resp.json()
        assert resp['error'] == const.ACCESS_DENIED


    @pytest.mark.negative
    def test_upload_team_icon_outsider(self):
        resp = func.add_team(self.api)
        api2 = auth.login_another_user(self.url, self.phone4, self.code4)
        resp = api2.upload_team_icon(resp['uid'], os.path.join(const.TD_FILES, 'tiger.jpg'))
        resp = resp.json()
        assert resp['error'] == const.ACCESS_DENIED


    @pytest.mark.negative
    @pytest.mark.parametrize("filename", [
        'tiger.pdf',
        'tiger.ico'
    ])
    def test_upload_team_icon_invalid(self, filename):
        resp = func.add_team(self.api)
        resp = self.api.upload_team_icon(resp['uid'], os.path.join(const.TD_FILES, filename))
        resp = resp.json()
        assert const.INVALID_DATA == resp['error']
        assert 'Ошибка при загрузке. Пожалуйста, попробуйте ещё раз' == resp['details']['file']


    @pytest.mark.positive
    @pytest.mark.parametrize("exist", [
        'icon_exist',
        'icon_not_exist'
    ])
    def test_delete_team_icon(self, exist):
        resp = func.add_team(self.api)
        team_uid = resp['uid']
        if exist == 'icon_exist':
            self.api.upload_team_icon(team_uid, os.path.join(const.TD_FILES, 'tiger.jpg'))
        resp = self.api.delete_team_icon(team_uid)
        resp = resp.json()
        assert 'error' not in resp
        assert resp['result']['lg'] == None
        assert resp['result']['sm'] == None


    @pytest.mark.negative
    def test_delete_team_icon_member(self):
        team_uid = func.add_team(self.api)['uid']
        func.add_contact(self.api, team_uid, self.phone2, role='member')
        api2 = auth.login_another_user(self.url, self.phone2, self.code2)
        resp = api2.delete_team_icon(team_uid).json()
        assert resp['error'] == const.ACCESS_DENIED


    @pytest.mark.negative
    def test_delete_team_icon_outsider(self):
        resp = func.add_team(self.api)
        team_uid = resp['uid']
        api2 = auth.login_another_user(self.url, self.phone4, self.code4)
        resp = api2.delete_team_icon(team_uid)
        resp = resp.json()
        assert resp['error'] == const.ACCESS_DENIED


    @pytest.mark.positive
    def test_get_team_valid_uid(self):
        resp = func.add_team(self.api)
        team_uid = resp['uid']
        name = resp['name']
        resp = self.api.get_team(team_uid)
        resp = resp.json()
        assert 'error' not in resp
        assert resp['result']['uid'] == team_uid
        assert resp['result']['name'] == name


    @pytest.mark.negative
    def test_get_team_invalid_uid(self):
        resp = self.api.get_team(self.invalid_team_uid)
        resp = resp.json()
        assert resp['error'] == 'NOT_FOUND'


    @pytest.mark.positive
    def test_get_team_member(self):
        team = func.add_team(self.api)
        team_uid = team['uid']
        name = team['name']
        func.add_contact(self.api, team_uid, self.phone2, role='member')
        api2 = auth.login_another_user(self.url, self.phone2, self.code2)
        resp = api2.get_team(team_uid).json()
        assert 'error' not in resp
        assert resp['result']['uid'] == team_uid
        assert resp['result']['name'] == name


    @pytest.mark.negative
    def test_get_team_valid_uid_outsider(self):
        resp = func.add_team(self.api)
        team_uid = resp['uid']
        api2 = auth.login_another_user(self.url, self.phone4, self.code4)
        resp = api2.delete_team(team_uid)
        resp = resp.json()
        assert resp['error'] == const.ACCESS_DENIED


    @pytest.mark.positive
    def test_edit_team_name_valid(self):
        resp = func.add_team(self.api)
        team_uid = resp['uid']
        new_name = 'new_' + tools.generate_random_string()
        data = {'name': new_name}
        resp = self.api.edit_team(team_uid, data)
        resp = resp.json()
        assert 'error' not in resp
        assert resp['result']['uid'] == team_uid
        assert resp['result']['name'] == new_name


    @pytest.mark.negative
    def test_edit_team_name_member(self):
        team = func.add_team(self.api)
        team_uid = team['uid']
        func.add_contact(self.api, team_uid, self.phone2, role='member')
        new_name = 'new_' + tools.generate_random_string()
        data = {'name': new_name}
        api2 = auth.login_another_user(self.url, self.phone2, self.code2)
        resp = api2.edit_team(team_uid, data).json()
        assert resp['error'] == const.ACCESS_DENIED


    @pytest.mark.negative
    def test_edit_team_name_outsider(self):
        resp = func.add_team(self.api)
        team_uid = resp['uid']
        new_name = 'new_' + tools.generate_random_string()
        data = {'name': new_name}
        api2 = auth.login_another_user(self.url, self.phone4, self.code4)
        resp = api2.edit_team(team_uid, data)
        resp = resp.json()
        assert resp['error'] == const.ACCESS_DENIED


    @pytest.mark.negative
    def test_edit_team_name_empty(self):
        resp = func.add_team(self.api)
        team_uid = resp['uid']
        data = {'name': ''}
        resp = self.api.edit_team(team_uid, data)
        resp = resp.json()
        assert resp['error'] == const.INVALID_DATA
        assert resp['details']['name'] == 'Обязательное поле.'


    @pytest.mark.positive
    def test_delete_exist_team(self):
        resp = func.add_team(self.api)
        team_uid = resp['uid']
        resp = self.api.delete_team(team_uid)
        resp = resp.json()
        resp2 = self.api.get_teams()
        resp2 = resp2.json()
        assert 'error' not in resp
        assert resp['result']['is_archive']
        assert resp['result']['uid'] == team_uid
        for item in resp2['result']:
            assert team_uid != item['uid']


    @pytest.mark.negative
    def test_delete_exist_team_member(self):
        team = func.add_team(self.api)
        team_uid = team['uid']
        func.add_contact(self.api, team_uid, self.phone2, role='member')
        api2 = auth.login_another_user(self.url, self.phone2, self.code2)
        resp = api2.delete_team(team_uid).json()
        assert resp['error'] == const.ACCESS_DENIED


    @pytest.mark.negative
    def test_delete_exist_team_outsider(self):
        resp = func.add_team(self.api)
        team_uid = resp['uid']
        api2 = auth.login_another_user(self.url, self.phone4, self.code4)
        resp = api2.delete_team(team_uid)
        resp = resp.json()
        assert resp['error'] == const.ACCESS_DENIED


    @pytest.mark.negative
    def test_delete_not_exist_team(self):
        resp = self.api.delete_team(self.invalid_team_uid)
        resp = resp.json()
        assert resp['error'] == 'NOT_FOUND'


    @pytest.mark.positive
    def test_get_usage_exist_team(self):
        resp = func.add_team(self.api)
        team_uid = resp['uid']
        resp = self.api.get_team_usage(team_uid)
        resp = resp.json()
        assert 'error' not in resp
        assert resp['result']['uploads_size'] == 0
        assert resp['result']['uploads_size_limit'] == 1073741824


    @pytest.mark.negative
    def test_get_usage_exist_team_member(self):
        team = func.add_team(self.api)
        team_uid = team['uid']
        func.add_contact(self.api, team_uid, self.phone2, role='member')
        api2 = auth.login_another_user(self.url, self.phone2, self.code2)
        resp = api2.get_team_usage(team_uid).json()
        assert resp['error'] == const.ACCESS_DENIED


    @pytest.mark.negative
    def test_get_usage_not_exist_team(self):
        resp = self.api.get_team_usage(self.invalid_team_uid)
        resp = resp.json()
        assert resp['error'] == 'NOT_FOUND'


    @pytest.mark.negative
    def test_get_usage_exist_team_outsider(self):
        resp = func.add_team(self.api)
        team_uid = resp['uid']
        api2 = auth.login_another_user(self.url, self.phone4, self.code4)
        resp = api2.get_team_usage(team_uid)
        resp = resp.json()
        assert resp['error'] == const.ACCESS_DENIED


    @pytest.mark.positive
    def test_send_help(self):
        team = func.add_team(self.api)
        team_uid = team['uid']
        email = 'hello@hello.ru'
        text = 'I need help'
        resp = self.api.send_help(team_uid, email, text).json()
        assert 'error' not in resp
        assert resp['result'] == 'OK'


    @pytest.mark.positive
    def test_send_help_member(self):
        team = func.add_team(self.api)
        team_uid = team['uid']
        func.add_contact(self.api, team_uid, self.phone2, role='member')
        email = 'hello_member@hello.ru'
        text = 'I need help. This is member of team.'
        api2 = auth.login_another_user(self.url, self.phone2, self.code2)
        resp = api2.send_help(team_uid, email, text).json()
        assert 'error' not in resp
        assert resp['result'] == 'OK'


    @pytest.mark.negative
    def test_send_help_outsider(self):
        team = func.add_team(self.api)
        team_uid = team['uid']
        email = 'hello_outsider@hello.ru'
        text = 'I need help, outsider'
        api4 = auth.login_another_user(self.url, self.phone4, self.code4)
        resp = api4.send_help(team_uid, email, text).json()
        assert resp['error'] == const.ACCESS_DENIED


    @pytest.mark.positive
    def test_send_help_upload(self):
        team = func.add_team(self.api)
        team_uid = team['uid']
        filename = 'tiger.jpg'
        resp = self.api.send_help_upload(team_uid,  os.path.join(const.TD_FILES, filename)).json()
        assert 'error' not in resp
        assert resp['result']['name'] == filename
        assert filename in resp['result']['url']
        assert resp['result']['size'] == 456822


    @pytest.mark.positive
    def test_send_help_upload_member(self):
        team = func.add_team(self.api)
        team_uid = team['uid']
        func.add_contact(self.api, team_uid, self.phone2, role='member')
        api2 = auth.login_another_user(self.url, self.phone2, self.code2)
        filename = 'word.docx'
        resp = api2.send_help_upload(team_uid,  os.path.join(const.TD_FILES, filename)).json()
        assert 'error' not in resp
        assert resp['result']['name'] == filename
        assert filename in resp['result']['url']
        assert resp['result']['size'] == 11573


    @pytest.mark.negative
    def test_send_help_upload_outsider(self):
        team = func.add_team(self.api)
        team_uid = team['uid']
        api4 = auth.login_another_user(self.url, self.phone4, self.code4)
        filename = 'word.docx'
        resp = api4.send_help_upload(team_uid,  os.path.join(const.TD_FILES, filename)).json()
        assert resp['error'] == const.ACCESS_DENIED

