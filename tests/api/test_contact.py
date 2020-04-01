import pytest
import os
import json

from helpers.api import API
from helpers.readers import read_yaml
import helpers.const as const
import helpers.auth as auth
import helpers.tools as tools
import helpers.functions as func


class TestsContact:
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
    team_uid = ''
    invalid_section_uid = '00000000-0000-0000-0000-982d4bac29a1'
    invalid_user_jid = '00000000-0000-0000-0000-77dc6850e494@xmpp'


    def setup_class(self):
        # Логин и создание команды, далее эта команда используется в тестах
        self.url = self.config['api']['url']
        phone = self.user['phone']
        code = self.user['code']
        auth_cookies = auth.login_with_cookies(self.url, phone, code)
        self.api = API(self.url, auth_cookies, is_token_auth=False)
        resp = func.add_team(self.api)
        self.team_uid = resp['uid']


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
    def test_add_section_with_empty_name(self):
        data = {'name': ''}
        resp = self.api.add_section(self.team_uid, data)
        resp = resp.json()
        assert const.INVALID_DATA == resp['error']
        assert 'Обязательное поле.' == resp['details']['name']


    @pytest.mark.positive
    def test_add_section_with_name_one_symbol(self):
        name = tools.generate_random_string(2)
        data = {'name': name}
        resp = self.api.add_section(self.team_uid, data)
        resp = resp.json()
        assert 'error' not in resp
        assert resp['result']['name'] == name


    @pytest.mark.positive
    def test_add_section_with_name_200_symbols(self):
        name = tools.generate_random_string(201)
        data = {'name': name}
        resp = self.api.add_section(self.team_uid, data)
        resp = resp.json()
        assert 'error' not in resp
        assert resp['result']['name'] == name


    @pytest.mark.negative
    def test_add_team_with_name_201_symbols(self):
        data = {'name': tools.generate_random_string(202)}
        resp = self.api.add_section(self.team_uid, data)
        resp = resp.json()
        assert const.INVALID_DATA == resp['error']
        assert 'Убедитесь, что это значение содержит не более 200 символов (сейчас 201).' == resp['details']['name']


    @pytest.mark.positive
    @pytest.mark.parametrize("first_symbol", [
        '1', '@', '#', '_ _', 'а', 'Я'
    ])
    def test_add_section_with_name_start_with(self, first_symbol):
        name = first_symbol + tools.generate_random_string(30)
        data = {'name': name}
        resp = self.api.add_section(self.team_uid, data)
        resp = resp.json()
        assert 'error' not in resp
        assert resp['result']['name'] == name


    @pytest.mark.negative
    @pytest.mark.parametrize("move", [
        'move_after',
        'move_before'
    ])
    def test_add_section_move_after_before_invalid(self, move):
        data = {'name': 'hello',
                move: self.invalid_section_uid}
        resp = self.api.add_section(self.team_uid, data)
        resp = resp.json()
        assert const.INVALID_DATA == resp['error']
        assert 'Секция не найдена' == resp['details'][move]


    @pytest.mark.positive
    def test_add_section_move_after(self):
        resp = self.api.get_sections(self.team_uid).json()
        after_uid = resp['result'][-1]['uid']
        name = 'after_' + tools.generate_random_string(10)
        data = {'name': name,
                'move_after': after_uid}
        resp = self.api.add_section(self.team_uid, data).json()
        current_uid = resp['result']['uid']
        resp = self.api.get_sections(self.team_uid)
        resp = resp.json()
        assert 'error' not in resp
        assert resp['result'][-2]['uid'] == after_uid
        assert resp['result'][-1]['uid'] == current_uid


    @pytest.mark.positive
    def test_add_section_move_before(self):
        resp = self.api.get_sections(self.team_uid).json()
        before_uid = resp['result'][0]['uid']
        name = 'before_' + tools.generate_random_string(10)
        data = {'name': name,
                'move_before': before_uid}
        resp = self.api.add_section(self.team_uid, data).json()
        current_uid = resp['result']['uid']
        resp = self.api.get_sections(self.team_uid)
        resp = resp.json()
        assert 'error' not in resp
        assert resp['result'][1]['uid'] == before_uid
        assert resp['result'][0]['uid'] == current_uid


    @pytest.mark.positive
    def test_get_sections(self):
        resp = self.api.get_sections(self.team_uid)
        resp = resp.json()
        assert 'error' not in resp
        for item in resp['result']:
            assert 'name' in item


    @pytest.mark.positive
    def test_get_sections_member(self):
        team_uid = func.add_team(self.api)['uid']
        func.add_contact(self.api, team_uid, self.phone2, 'member')['jid']
        api2 = auth.login_another_user(self.url, self.phone2, self.code2)
        resp = api2.get_sections(team_uid)
        resp = resp.json()
        assert 'error' not in resp
        for item in resp['result']:
            assert 'name' in item


    @pytest.mark.negative
    def test_get_sections_outsider(self):
        api2 = auth.login_another_user(self.url, self.phone4, self.code4)
        resp = api2.get_sections(self.team_uid)
        resp = resp.json()
        assert resp['error'] == const.ACCESS_DENIED


    @pytest.mark.negative
    @pytest.mark.parametrize("move", [
        'move_after',
        'move_before'
    ])
    def test_move_section_invalid(self, move):
        section_uid = func.add_section(self.api, self.team_uid)['uid']
        if move == 'move_after':
            resp = self.api.set_section_move_after(self.team_uid,
                                                   self.invalid_section_uid,
                                                   section_uid)
        else:
            resp = self.api.set_section_move_before(self.team_uid,
                                                   section_uid,
                                                   self.invalid_section_uid)
        resp = resp.json()
        assert resp['error'] == const.ACCESS_DENIED
        assert 'section "{uid}" not found'.format(uid=self.invalid_section_uid) == resp['details']


    @pytest.mark.positive
    def test_move_section_move_after(self):
        resp = self.api.get_sections(self.team_uid).json()
        after_uid = resp['result'][-1]['uid']
        name = 'after_' + tools.generate_random_string(10)
        data = {'name': name,
                'move_after': after_uid}
        resp = self.api.add_section(self.team_uid, data).json()
        current_uid = resp['result']['uid']
        self.api.set_section_move_after(self.team_uid, current_uid, after_uid)
        resp = self.api.get_sections(self.team_uid)
        resp = resp.json()
        assert 'error' not in resp
        assert resp['result'][-2]['uid'] == after_uid
        assert resp['result'][-1]['uid'] == current_uid


    @pytest.mark.positive
    def test_move_section_move_before(self):
        resp = self.api.get_sections(self.team_uid).json()
        before_uid = resp['result'][0]['uid']
        name = 'before_' + tools.generate_random_string(10)
        data = {'name': name,
                'move_after': before_uid}
        resp = self.api.add_section(self.team_uid, data).json()
        current_uid = resp['result']['uid']
        self.api.set_section_move_before(self.team_uid, current_uid, before_uid)
        resp = self.api.get_sections(self.team_uid)
        resp = resp.json()
        assert 'error' not in resp
        assert resp['result'][1]['uid'] == before_uid
        assert resp['result'][0]['uid'] == current_uid


    @pytest.mark.positive
    def test_move_section_move_before_admin(self):
        team_uid = func.add_team(self.api)['uid']
        func.add_contact(self.api, team_uid, self.phone2, 'admin')
        resp = self.api.get_sections(team_uid).json()
        before_uid = resp['result'][0]['uid']
        name = 'before_' + tools.generate_random_string(10)
        data = {'name': name,
                'move_after': before_uid}
        resp = self.api.add_section(team_uid, data).json()
        current_uid = resp['result']['uid']
        api2 = auth.login_another_user(self.url, self.phone2, self.code2)
        resp = api2.set_section_move_before(team_uid, current_uid, before_uid).json()
        resp = self.api.get_sections(team_uid)
        resp = resp.json()
        assert 'error' not in resp
        assert resp['result'][1]['uid'] == before_uid
        assert resp['result'][0]['uid'] == current_uid


    @pytest.mark.negative
    def test_move_section_move_before_member(self):
        team_uid = func.add_team(self.api)['uid']
        func.add_contact(self.api, team_uid, self.phone2, 'member')
        resp = self.api.get_sections(team_uid).json()
        before_uid = resp['result'][0]['uid']
        name = 'before_' + tools.generate_random_string(10)
        data = {'name': name,
                'move_after': before_uid}
        resp = self.api.add_section(team_uid, data).json()
        current_uid = resp['result']['uid']
        api2 = auth.login_another_user(self.url, self.phone2, self.code2)
        resp = api2.set_section_move_before(team_uid, current_uid, before_uid).json()
        assert resp['error'] == const.ACCESS_DENIED


    @pytest.mark.negative
    def test_move_section_move_before_outsider(self):
        team_uid = func.add_team(self.api)['uid']
        resp = self.api.get_sections(team_uid).json()
        before_uid = resp['result'][0]['uid']
        name = 'before_' + tools.generate_random_string(10)
        data = {'name': name,
                'move_after': before_uid}
        resp = self.api.add_section(team_uid, data).json()
        current_uid = resp['result']['uid']
        api4 = auth.login_another_user(self.url, self.phone4, self.code4)
        resp = api4.set_section_move_before(team_uid, current_uid, before_uid).json()
        assert resp['error'] == const.ACCESS_DENIED


    @pytest.mark.positive
    def test_edit_section_without_param(self):
        data = {'name': tools.generate_random_string()}
        exp_dict = self.api.add_section(self.team_uid, data).json()
        section_uid = exp_dict['result']['uid']
        data = {}
        resp = self.api.edit_section(self.team_uid, section_uid, data).json()
        assert 'error' not in resp
        assert resp['result'] == exp_dict['result']


    @pytest.mark.negative
    def test_edit_section_invalid(self):
        data = {}
        resp = self.api.edit_section(self.team_uid, self.invalid_section_uid, data).json()
        assert resp['error'] == const.ACCESS_DENIED
        assert 'section "{uid}" not found'.format(uid=self.invalid_section_uid) == resp['details']


    @pytest.mark.negative
    def test_edit_section_with_empty_name(self):
        data = {'name': tools.generate_random_string()}
        exp_dict = self.api.add_section(self.team_uid, data).json()
        section_uid = exp_dict['result']['uid']
        data = {'name': ''}
        resp = self.api.edit_section(self.team_uid, section_uid, data).json()
        assert resp['error'] == const.INVALID_DATA
        assert 'Обязательное поле.' == resp['details']['name']


    @pytest.mark.positive
    def test_edit_section_with_name(self):
        data = {'name': tools.generate_random_string()}
        exp_dict = self.api.add_section(self.team_uid, data).json()
        section_uid = exp_dict['result']['uid']
        new_name = 'edit_' + tools.generate_random_string()
        data = {'name': new_name}
        resp = self.api.edit_section(self.team_uid, section_uid, data).json()
        assert 'error' not in resp
        assert resp['result']['uid'] == section_uid
        assert resp['result']['name'] == new_name


    @pytest.mark.positive
    def test_edit_section_with_name_admin(self):
        team_uid = func.add_team(self.api)['uid']
        func.add_contact(self.api, team_uid, self.phone2, 'admin')
        data = {'name': tools.generate_random_string()}
        exp_dict = self.api.add_section(team_uid, data).json()
        section_uid = exp_dict['result']['uid']
        new_name = 'edit_' + tools.generate_random_string()
        data = {'name': new_name}
        api2 = auth.login_another_user(self.url, self.phone2, self.code2)
        resp = api2.edit_section(team_uid, section_uid, data).json()
        assert 'error' not in resp
        assert resp['result']['uid'] == section_uid
        assert resp['result']['name'] == new_name


    @pytest.mark.negative
    def test_edit_section_with_name_member(self):
        team_uid = func.add_team(self.api)['uid']
        func.add_contact(self.api, team_uid, self.phone2, 'member')
        data = {'name': tools.generate_random_string()}
        exp_dict = self.api.add_section(team_uid, data).json()
        section_uid = exp_dict['result']['uid']
        new_name = 'edit_' + tools.generate_random_string()
        data = {'name': new_name}
        api2 = auth.login_another_user(self.url, self.phone2, self.code2)
        resp = api2.edit_section(team_uid, section_uid, data).json()
        assert resp['error'] == const.ACCESS_DENIED


    @pytest.mark.negative
    def test_edit_section_with_name_outsider(self):
        team_uid = func.add_team(self.api)['uid']
        data = {'name': tools.generate_random_string()}
        exp_dict = self.api.add_section(team_uid, data).json()
        section_uid = exp_dict['result']['uid']
        new_name = 'edit_' + tools.generate_random_string()
        data = {'name': new_name}
        api4 = auth.login_another_user(self.url, self.phone4, self.code4)
        resp = api4.edit_section(team_uid, section_uid, data).json()
        assert resp['error'] == const.ACCESS_DENIED


    @pytest.mark.positive
    def test_delete_exist_section(self):
        data = {'name': tools.generate_random_string()}
        exp_dict = self.api.add_section(self.team_uid, data).json()
        section_uid = exp_dict['result']['uid']
        resp = self.api.delete_section(self.team_uid, section_uid).json()
        resp2 = self.api.get_sections(self.team_uid).json()
        assert 'error' not in resp
        assert resp['result'] is None
        for item in resp2['result']:
            assert section_uid != item['uid']


    @pytest.mark.negative
    def test_delete_not_exist_section(self):
        resp = self.api.delete_section(self.team_uid, self.invalid_section_uid).json()
        assert resp['error'] == const.ACCESS_DENIED
        assert 'section "{uid}" not found'.format(uid=self.invalid_section_uid) == resp['details']


    @pytest.mark.negative
    def test_delete_exist_section_member(self):
        team_uid = func.add_team(self.api)['uid']
        func.add_contact(self.api, team_uid, self.phone2, 'member')
        api2 = auth.login_another_user(self.url, self.phone2, self.code2)
        data = {'name': tools.generate_random_string()}
        exp_dict = self.api.add_section(team_uid, data).json()
        section_uid = exp_dict['result']['uid']
        resp = api2.delete_section(team_uid, section_uid).json()
        assert resp['error'] == const.ACCESS_DENIED


    @pytest.mark.negative
    def test_delete_section_outsider(self):
        data = {'name': tools.generate_random_string()}
        exp_dict = self.api.add_section(self.team_uid, data).json()
        section_uid = exp_dict['result']['uid']
        api2 = auth.login_another_user(self.url, self.phone4, self.code4)
        resp = api2.delete_section(self.team_uid, section_uid).json()
        assert resp['error'] == const.ACCESS_DENIED


    @pytest.mark.negative
    def test_invite_one_contact_empty(self):
        resp = func.add_team(self.api)
        team_uid = resp['uid']
        data = {}
        resp = self.api.add_contacts(team_uid, data).json()
        assert resp['error'] == const.INVALID_DATA
        assert 'Обязательное поле.' == resp['details']['phone']


    @pytest.mark.positive
    def test_invite_one_contact_only_phone(self):
        resp = func.add_team(self.api)
        team_uid = resp['uid']
        data = {'phone': self.phone2}
        resp = self.api.add_contacts(team_uid, data).json()
        resp2 = self.api.get_contacts(team_uid).json()
        assert 'error' not in resp
        assert self.phone2 == resp['result']['contact_phone']
        assert self.phone2 == resp2['result'][0]['contact_phone']


    @pytest.mark.positive
    def test_invite_one_contact_all_params(self):
        team_uid = func.add_team(self.api)['uid']
        section_uid = func.add_section(self.api, team_uid)['uid']
        data = {'family_name': 'Фамилия',
                'given_name': 'Имя',
                'phone': self.phone2,
                'role': 'пресс-секретарь',
                'section': section_uid,
                'status': 'admin'}
        resp = self.api.add_contacts(team_uid, data).json()
        resp2 = self.api.get_contacts(team_uid).json()
        resp2 = resp2['result'][0]
        exp_data = {'family_name': resp2['family_name'],
                    'given_name': resp2['given_name'],
                    'phone': resp2['contact_phone'],
                    'role': resp2['role'],
                    'section': resp2['section_uid'],
                    'status': resp2['status']}
        assert 'error' not in resp
        assert self.phone2 == resp['result']['contact_phone']
        assert exp_data == data


    @pytest.mark.negative
    def test_invite_one_contact_section_invalid(self):
        resp = func.add_team(self.api)
        team_uid = resp['uid']
        data = {"phone": self.phone2,
                "section": self.invalid_section_uid}
        resp = self.api.add_contacts(team_uid, data).json()
        assert resp['error'] == const.INVALID_DATA
        assert "Некорректная секция: '{uid}'".format(uid=self.invalid_section_uid) == resp['details']['section']


    @pytest.mark.positive
    def test_invite_2_contacts_only_phone(self):
        resp = func.add_team(self.api)
        team_uid = resp['uid']
        data = {'contacts': [
            {'phone': self.phone2},
            {'phone': self.phone3}
        ]}
        data_json = json.dumps(data)
        resp = self.api.add_contacts(team_uid, data_json).json()
        assert 'error' not in resp
        assert self.phone2 == resp['result']['contacts'][0]['contact_phone']
        assert self.phone3 == resp['result']['contacts'][1]['contact_phone']


    @pytest.mark.positive
    def test_invite_2_contacts_all_params(self):
        team_uid = func.add_team(self.api)['uid']
        section_uid = func.add_section(self.api, team_uid)['uid']
        data = {'contacts': [
            {
                'family_name': 'Первов',
                'given_name': 'Первый',
                'phone': self.phone2,
                'role': 'пресс-секретарь',
                'section': section_uid,
                'status': 'admin'

            },
            {
                'family_name': 'Второв',
                'given_name': 'Второй',
                'phone': self.phone3,
                'role': 'член КПСС',
                'section': section_uid,
                "status": 'member'

            },
        ]}
        data_json = json.dumps(data)
        resp = self.api.add_contacts(team_uid, data_json).json()
        data1 = data['contacts'][0]
        data2 = data['contacts'][1]
        cont1 = resp['result']['contacts'][0]
        cont2 = resp['result']['contacts'][1]
        assert 'error' not in resp
        assert data1['family_name'] == cont1['family_name']
        assert data1['given_name'] == cont1['given_name']
        assert data1['phone'] == cont1['contact_phone']
        assert data1['role'] == cont1['role']
        assert data1['section'] == cont1['section_uid']
        assert data1['status'] == cont1['status']
        assert data2['family_name'] == cont2['family_name']
        assert data2['given_name'] == cont2['given_name']
        assert data2['phone'] == cont2['contact_phone']
        assert data2['role'] == cont2['role']
        assert data2['section'] == cont2['section_uid']
        assert data2['status'] == cont2['status']


    @pytest.mark.negative
    def test_invite_2_contacts_with_invalid_section_uid(self):
        team_uid = func.add_team(self.api)['uid']
        data = {'contacts': [
            {
                'phone': self.phone2,
                'section': self.invalid_section_uid,
            },
            {
                'phone': self.phone3,
                'section': self.invalid_section_uid,
            }
        ]}
        data_json = json.dumps(data)
        resp = self.api.add_contacts(team_uid, data_json).json()
        assert resp['error'] == const.INVALID_DATA
        assert "Некорректная секция: '{uid}'".format(uid=self.invalid_section_uid) == resp['details']['contacts'][0]['section']
        assert "Некорректная секция: '{uid}'".format(uid=self.invalid_section_uid) == resp['details']['contacts'][1]['section']


    @pytest.mark.positive
    def test_invite_2_contacts_with_different_section(self):
        team_uid = func.add_team(self.api)['uid']
        section_uid1 = func.add_section(self.api, team_uid)['uid']
        section_uid2 = func.add_section(self.api, team_uid)['uid']
        data = {'contacts': [
            {
                'phone': self.phone2,
                'section': section_uid1,
            },
            {
                'phone': self.phone3,
                'section': section_uid2,
            }
        ]}
        data_json = json.dumps(data)
        resp = self.api.add_contacts(team_uid, data_json).json()
        data1 = data['contacts'][0]
        data2 = data['contacts'][1]
        assert 'error' not in resp
        assert data1['phone'] == resp['result']['contacts'][0]['contact_phone']
        assert data1['section'] == resp['result']['contacts'][0]['section_uid']
        assert data2['phone'] == resp['result']['contacts'][1]['contact_phone']
        assert data2['section'] == resp['result']['contacts'][1]['section_uid']


    @pytest.mark.positive
    def test_invite_contact_member_admin(self):
        team_uid = func.add_team(self.api)['uid']
        data = {'phone': self.phone2,
                'status': 'admin'}
        self.api.add_contacts(team_uid, data)
        api2 = auth.login_another_user(self.url, self.phone2, self.code2)
        data = {'phone': self.phone3}
        resp = api2.add_contacts(team_uid, data).json()
        resp2 = self.api.get_contacts(team_uid).json()
        assert 'error' not in resp
        assert self.phone3 == resp['result']['contact_phone']
        assert self.phone3 == resp2['result'][0]['contact_phone']


    @pytest.mark.negative
    def test_invite_contact_member_not_admin(self):
        team_uid = func.add_team(self.api)['uid']
        data = {'phone': self.phone2,
                'status': 'member'}
        self.api.add_contacts(team_uid, data)
        api2 = auth.login_another_user(self.url, self.phone2, self.code2)
        data = {'phone': self.phone3}
        resp = api2.add_contacts(team_uid, data).json()
        assert resp['error'] == const.ACCESS_DENIED


    @pytest.mark.negative
    def test_invite_contact_outsider(self):
        team_uid = func.add_team(self.api)['uid']
        data = {'phone': self.phone2,
                'status': 'member'}
        self.api.add_contacts(team_uid, data)
        api2 = auth.login_another_user(self.url, self.phone4, self.code4)
        data = {'phone': self.phone3}
        resp = api2.add_contacts(team_uid, data).json()
        assert resp['error'] == const.ACCESS_DENIED


    @pytest.mark.positive
    def test_get_contacts(self):
        resp = self.api.get_contacts(self.team_uid)
        resp = resp.json()
        assert 'error' not in resp
        for item in resp['result']:
            assert 'contact_phone' in item


    @pytest.mark.positive
    @pytest.mark.parametrize("filename", [
        'tiger',
        'TIGER.JPEG',
        'tiger.jpg',
        'tiger.PNG',
    ])
    def test_upload_contact_icon_valid(self, filename):
        '''
        Пока доступны только PNG и JPG
        'tiger.bmp',
        'tiger.gif',
        'tiger.tiff'
        '''
        resp = self.api.get_contacts(self.team_uid).json()
        contact_jid = resp['result'][0]['jid']
        resp = self.api.upload_contact_icon(self.team_uid, contact_jid, os.path.join(const.TD_FILES, filename))
        resp = resp.json()
        assert 'error' not in resp
        assert resp['result']['lg']['url']
        assert resp['result']['sm']['url']


    @pytest.mark.negative
    @pytest.mark.parametrize("filename", [
        'tiger.pdf',
        'tiger.ico'
    ])
    def test_upload_contact_icon_invalid(self, filename):
        resp = self.api.get_contacts(self.team_uid).json()
        contact_jid = resp['result'][0]['jid']
        resp = self.api.upload_contact_icon(self.team_uid, contact_jid, os.path.join(const.TD_FILES, filename))
        resp = resp.json()
        assert const.INVALID_DATA == resp['error']
        assert 'Ошибка при загрузке. Пожалуйста, попробуйте ещё раз' == resp['details']['file']


    @pytest.mark.negative
    def test_upload_contact_icon_another_user(self):
        resp = self.api.get_contacts(self.team_uid).json()
        contact_jid = resp['result'][0]['jid']
        api2 = auth.login_another_user(self.url, self.phone4, self.code4)
        resp = api2.upload_contact_icon(self.team_uid, contact_jid, os.path.join(const.TD_FILES, 'tiger.jpg'))
        resp = resp.json()
        assert const.ACCESS_DENIED == resp['error']


    @pytest.mark.positive
    @pytest.mark.parametrize("exist", [
        'icon_exist',
        'icon_not_exist'
    ])
    def test_delete_contact_icon(self, exist):
        team_uid = func.add_team(self.api)['uid']
        resp = self.api.get_contacts(self.team_uid).json()
        contact_jid = resp['result'][0]['jid']
        if exist == 'icon_exist':
            self.api.upload_contact_icon(team_uid, contact_jid, os.path.join(const.TD_FILES, 'tiger.jpg'))
        resp = self.api.delete_contact_icon(self.team_uid, contact_jid)
        resp = resp.json()
        assert 'error' not in resp
        assert resp['result']['lg'] == None
        assert resp['result']['sm'] == None


    @pytest.mark.negative
    def test_delete_contact_icon_another_user(self):
        team_uid = func.add_team(self.api)['uid']
        resp = self.api.get_contacts(team_uid).json()
        contact_jid = resp['result'][0]['jid']
        api2 = auth.login_another_user(self.url, self.phone4, self.code4)
        resp = api2.delete_contact_icon(self.team_uid, contact_jid)
        resp = resp.json()
        assert const.ACCESS_DENIED == resp['error']


    @pytest.mark.positive
    def test_get_contact_valid_jid(self):
        resp = self.api.get_contacts(self.team_uid).json()
        contact_jid = resp['result'][0]['jid']
        phone = resp['result'][0]['contact_phone']
        resp = self.api.get_contact(self.team_uid, contact_jid).json()
        assert 'error' not in resp
        assert contact_jid == resp['result']['jid']
        assert phone == resp['result']['contact_phone']


    @pytest.mark.negative
    def test_get_contact_invalid_jid(self):
        resp = self.api.get_contact(self.team_uid, self.invalid_user_jid).json()
        assert const.NOT_FOUND == resp['error']


    @pytest.mark.positive
    @pytest.mark.parametrize("role", [
        'admin',
        'member'
    ])
    def test_get_contact_another_user_role(self, role):
        team_uid = func.add_team(self.api)['uid']
        data = {'phone': self.phone2,
                'status': role}
        self.api.add_contacts(team_uid, data)
        resp = self.api.get_contacts(team_uid).json()
        contact_jid = resp['result'][1]['jid']
        api2 = auth.login_another_user(self.url, self.phone2, self.code2)
        resp = api2.get_contact(team_uid, contact_jid).json()
        assert 'error' not in resp
        assert contact_jid == resp['result']['jid']


    @pytest.mark.negative
    def test_get_contact_outsider(self):
        team_uid = func.add_team(self.api)['uid']
        resp = self.api.get_contacts(team_uid).json()
        contact_jid = resp['result'][0]['jid']
        api2 = auth.login_another_user(self.url, self.phone2, self.code2)
        resp = api2.get_contact(team_uid, contact_jid).json()
        assert const.ACCESS_DENIED == resp['error']


    @pytest.mark.positive
    def test_edit_contact_valid(self):
        team_uid = func.add_team(self.api)['uid']
        data = {'phone': self.phone2}
        self.api.add_contacts(team_uid, data)
        resp = self.api.get_contacts(team_uid).json()
        contact_jid = resp['result'][0]['jid']
        data = {'family_name': 'Brown',
                'given_name': 'Jack',
                'contact_phone': '+70000000000',
                'role': 'Secret Agent',
                'status': 'admin',
                'contact_email': 'o@o.com'}
        res = self.api.edit_contact(team_uid, contact_jid, data).json()
        resp = res['result']
        exp_data = {'family_name': resp['family_name'],
                    'given_name': resp['given_name'],
                    'contact_phone': resp['contact_phone'],
                    'role': resp['role'],
                    'status': resp['status'],
                    'contact_email': resp['contact_email']}
        assert 'error' not in res
        assert data == exp_data


    @pytest.mark.positive
    def test_edit_contact_with_empty_data(self):
        team_uid = func.add_team(self.api)['uid']
        data = {'phone': self.phone2}
        self.api.add_contacts(team_uid, data)
        resp = self.api.get_contacts(team_uid).json()
        contact_jid = resp['result'][0]['jid']
        act_data = {'family_name': resp['result'][0]['family_name'],
                    'given_name': resp['result'][0]['given_name'],
                    'contact_phone': resp['result'][0]['contact_phone'],
                    'role': resp['result'][0]['role'],
                    'status': resp['result'][0]['status'],
                    'contact_email': resp['result'][0]['contact_email']}
        data = {}
        res = self.api.edit_contact(team_uid, contact_jid, data).json()
        resp = res['result']
        exp_data = {'family_name': resp['family_name'],
                    'given_name': resp['given_name'],
                    'contact_phone': resp['contact_phone'],
                    'role': resp['role'],
                    'status': resp['status'],
                    'contact_email': resp['contact_email']}
        assert 'error' not in res
        assert act_data == exp_data


    @pytest.mark.positive
    def test_edit_contact_another_user_admin(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # добавляем контакт с правами админа
        data = {'phone': self.phone2,
                'status': 'admin'}
        self.api.add_contacts(team_uid, data)
        # получаем jid овнера команды
        resp = self.api.get_contacts(team_uid).json()
        contact_jid = resp['result'][1]['jid']
        # изменяем контакт овнера вторым узером админом
        api2 = auth.login_another_user(self.url, self.phone2, self.code2)
        data = {'family_name': 'Test'}
        resp = api2.edit_contact(team_uid, contact_jid, data).json()
        assert 'error' not in resp
        assert data['family_name'] == resp['result']['family_name']


    @pytest.mark.negative
    def test_edit_contact_another_user_not_admin(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # добавляем контакт с правами админа
        data = {'phone': self.phone2,
                'status': 'member'}
        self.api.add_contacts(team_uid, data)
        # получаем jid овнера команды
        resp = self.api.get_contacts(team_uid).json()
        contact_jid = resp['result'][1]['jid']
        # изменяем контакт овнера вторым узером админом
        api2 = auth.login_another_user(self.url, self.phone2, self.code2)
        data = {'family_name': 'Test'}
        resp = api2.edit_contact(team_uid, contact_jid, data).json()
        assert const.ACCESS_DENIED == resp['error']


    @pytest.mark.negative
    def test_edit_contact_outsider(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # получаем jid овнера команды
        resp = self.api.get_contacts(team_uid).json()
        contact_jid = resp['result'][0]['jid']
        # изменяем контакт овнера пользователем не состоящим в команде
        api2 = auth.login_another_user(self.url, self.phone2, self.code2)
        data = {'family_name': 'Test'}
        resp = api2.edit_contact(team_uid, contact_jid, data).json()
        assert const.ACCESS_DENIED == resp['error']


    @pytest.mark.positive
    def test_delete_exist_contact(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # добавляем контакт с правами админа
        data = {'phone': self.phone2,
                'status': 'admin'}
        self.api.add_contacts(team_uid, data)
        # получаем jid нового контакта команды
        resp = self.api.get_contacts(team_uid).json()
        contact_jid = resp['result'][0]['jid']
        resp = self.api.delete_contact(team_uid, contact_jid).json()
        resp2 = self.api.get_contacts(team_uid).json()
        assert 'error' not in resp
        assert resp['result']['is_archive']
        assert resp2['result'][0]['is_archive']
        assert contact_jid == resp2['result'][0]['jid']


    @pytest.mark.negative
    def test_delete_not_exist_contact(self):
        team_uid = func.add_team(self.api)['uid']
        resp = self.api.delete_contact(team_uid, self.invalid_user_jid).json()
        assert const.NOT_FOUND == resp['error']


    @pytest.mark.positive
    def test_delete_contact_another_user_admin(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # добавляем контакт с правами админа
        data = {'phone': self.phone2,
                'status': 'admin'}
        self.api.add_contacts(team_uid, data)
        # добавляем контакт с обычными правами
        data = {'phone': self.phone3,
                'status': 'member'}
        self.api.add_contacts(team_uid, data)
        # получаем jid последнего добавленного участника
        resp = self.api.get_contacts(team_uid).json()
        contact_jid = resp['result'][0]['jid']
        # удаляем контакт вторым узером админом
        api2 = auth.login_another_user(self.url, self.phone2, self.code2)
        resp = api2.delete_contact(team_uid, contact_jid).json()
        resp2 = api2.get_contacts(team_uid).json()
        assert 'error' not in resp
        assert resp['result']['is_archive']
        assert resp2['result'][0]['is_archive']
        assert contact_jid == resp2['result'][0]['jid']


    @pytest.mark.negative
    def test_delete_contact_outsider(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # получаем jid овнера команды
        resp = self.api.get_contacts(team_uid).json()
        contact_jid = resp['result'][0]['jid']
        # пытаемся удалить контакт овнера пользователем из другой команды
        api2 = auth.login_another_user(self.url, self.phone2, self.code2)
        resp = api2.delete_contact(team_uid, contact_jid).json()
        assert const.ACCESS_DENIED == resp['error']

