import pytest
import os
import json

from helpers.api import API
from helpers.readers import read_yaml
import helpers.const as const
import helpers.auth as auth
import helpers.tools as tools
import helpers.functions as func


class TestsGroup:
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
    invalid_user_jid = '00000000-0000-0000-0000-77dc6850e494@xmpp'
    invalid_group_jid = '00000000-0000-0000-0000-f9cf5a136508@conference.xmpp'
    invalid_team_uid = '00000000-0000-0000-0000-982d4bac29a1'


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
    def test_add_group_without_params(self):
        data = {}
        resp = self.api.add_group(self.team_uid, data).json()
        assert const.INVALID_DATA == resp['error']
        assert 'Обязательное поле.' == resp['details']['display_name']


    @pytest.mark.negative
    def test_add_group_with_empty_name(self):
        data = {'display_name': ''}
        resp = self.api.add_group(self.team_uid, data).json()
        assert const.INVALID_DATA == resp['error']
        assert 'Обязательное поле.' == resp['details']['display_name']


    @pytest.mark.positive
    def test_add_group_with_name_one_symbol(self):
        name = tools.generate_random_string(2)
        data = {'display_name': name}
        resp = self.api.add_group(self.team_uid, data).json()
        assert 'error' not in resp
        assert resp['result']['display_name'] == name


    @pytest.mark.positive
    def test_add_group_with_name_255_symbols(self):
        name = tools.generate_random_string(256)
        data = {'display_name': name}
        resp = self.api.add_group(self.team_uid, data).json()
        assert 'error' not in resp
        assert resp['result']['display_name'] == name


    @pytest.mark.negative
    def test_add_group_with_name_256_symbols(self):
        name = tools.generate_random_string(257)
        data = {'display_name': name}
        resp = self.api.add_group(self.team_uid, data).json()
        assert const.INVALID_DATA == resp['error']
        assert 'Убедитесь, что это значение содержит не более 255 символов (сейчас 256).' == resp['details']['display_name']


    @pytest.mark.positive
    @pytest.mark.parametrize("first_symbol", [
        '1', '@', '#', '_ _', 'а', 'Я'
    ])
    def test_add_group_with_name_start_with(self, first_symbol):
        name = first_symbol + tools.generate_random_string(30)
        data = {'display_name': name}
        resp = self.api.add_group(self.team_uid, data).json()
        assert 'error' not in resp
        assert resp['result']['display_name'] == name


    @pytest.mark.positive
    def test_add_group_with_all_params(self):
        name = tools.generate_random_string(30)
        data = {'display_name': name,
                'description': 'group description',
                'readonly_for_members': False,
                'api_enabled': True,
                'default_for_all': True,
                'public': True}
        resp = self.api.add_group(self.team_uid, data).json()
        group_jid = resp['result']['jid']
        resp2 = self.api.get_group(self.team_uid, group_jid).json()
        resp2 = resp2['result']
        exp_data = {'display_name': resp2['display_name'],
                    'description': resp2['description'],
                    'readonly_for_members': resp2['readonly_for_members'],
                    'api_enabled': resp2['api_enabled'],
                    'default_for_all': resp2['default_for_all'],
                    'public': resp2['public']}
        assert 'error' not in resp
        assert resp['result']['display_name'] == name
        assert exp_data == data


    @pytest.mark.positive
    def test_add_group_with_invite_exist_member(self):
        resp = func.add_team_with_contact(self.api, phone=self.phone2)
        team_uid = resp['team_uid']
        user_jid = resp['member']['jid']
        group_name = 'gr_' + tools.generate_random_string(30)
        data = {'display_name': group_name,
                'members': [
                    {
                        'jid': resp['member']['jid'],
                        'status': resp['member']['status']
                    }
                ]
                }
        data_json = json.dumps(data)
        resp = self.api.add_group(team_uid, data_json).json()
        group_jid = resp['result']['jid']
        resp2 = self.api.get_group(team_uid, group_jid).json()
        assert data['display_name'] == resp2['result']['display_name']
        assert tools.is_items_exist_in_list_of_dict(
            resp2['result']['members'],
            'jid',
            user_jid)


    @pytest.mark.negative
    def test_add_group_with_invite_not_exist_member(self):
        group_name = 'gr_' + tools.generate_random_string(30)
        data = {'display_name': group_name,
                'members': [
                    {
                        'jid': self.invalid_user_jid,
                        'status': 'member'
                    }
                ]
                }
        data_json = json.dumps(data)
        resp = self.api.add_group(self.team_uid, data_json).json()
        assert const.INVALID_DATA == resp['error']
        assert 'Выберите корректный вариант. {jid} нет среди допустимых значений.'\
                   .format(jid=self.invalid_user_jid) == resp['details']['members'][0]['jid']


    @pytest.mark.positive
    def test_get_groups(self):
        func.add_group(self.api, self.team_uid)
        resp = self.api.get_groups(self.team_uid).json()
        assert 'error' not in resp
        for item in resp['result']:
            assert 'display_name' in item


    @pytest.mark.negative
    def test_get_groups_invalid_jid(self):
        resp = self.api.get_groups(self.invalid_group_jid).json()
        assert resp['error'] == const.NOT_FOUND


    @pytest.mark.positive
    def test_invite_member_in_group_role_owner(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # добавляем участников
        user2_jid = func.add_contact(self.api, team_uid, self.phone2)['jid']
        # создаем группу
        group_jid = func.add_group(self.api, team_uid)['jid']
        # приглашаем участников в группу
        data = {
                'jid': user2_jid,
                'status': 'admin'
            }
        resp = self.api.add_members(team_uid, group_jid, data).json()
        resp2 = self.api.get_groups(team_uid).json()
        resp2 = resp2['result'][0]['members']
        assert 'error' not in resp
        assert tools.is_items_exist_in_list_of_dict(
            resp2,
            'jid',
            user2_jid)


    @pytest.mark.positive
    def test_invite_member_in_group_role_admin(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # добавляем участников
        user2_jid = func.add_contact(self.api, team_uid, self.phone2)['jid']
        user3_jid = func.add_contact(self.api, team_uid, self.phone3)['jid']
        # создаем группу
        group_jid = func.add_group(self.api, team_uid)['jid']
        # приглашаем участника админа в группу
        data = {
            'jid': user2_jid,
            'status': 'admin'
        }
        self.api.add_members(team_uid, group_jid, data).json()
        # логинимся приглашенным пользователем админом
        auth_cookies = auth.login_with_cookies(self.url, self.phone2, self.code2)
        api2 = API(self.url, auth_cookies, is_token_auth=False)
        # приглашаем обычного участника в группу от админа
        data = {
            'jid': user3_jid,
            'status': 'member'
        }
        resp = api2.add_members(team_uid, group_jid, data).json()
        resp2 = api2.get_groups(team_uid).json()
        assert 'error' not in resp
        assert tools.is_items_exist_in_list_of_dict(
            resp2['result'][0]['members'],
            'jid',
            user3_jid)


    @pytest.mark.negative
    def test_invite_member_in_group_role_member(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # добавляем участников
        user2_jid = func.add_contact(self.api, team_uid, self.phone2)['jid']
        user3_jid = func.add_contact(self.api, team_uid, self.phone3)['jid']
        # создаем группу
        group_jid = func.add_group(self.api, team_uid)['jid']
        # приглашаем участника в группу
        data = {
            'jid': user2_jid,
            'status': 'member'
        }
        self.api.add_members(team_uid, group_jid, data).json()
        # логинимся приглашенным пользователем
        auth_cookies = auth.login_with_cookies(self.url, self.phone2, self.code2)
        api2 = API(self.url, auth_cookies, is_token_auth=False)
        # приглашаем обычного участника в группу от обычного участника
        data = {
            'jid': user3_jid,
            'status': 'member'
        }
        resp = api2.add_members(team_uid, group_jid, data).json()
        assert resp['error'] == const.ACCESS_DENIED


    @pytest.mark.negative
    def test_invite_member_in_group_invalid_jid(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # создаем группу
        group_jid = func.add_group(self.api, team_uid)['jid']
        # приглашаем участника админа в группу
        data = {
            'jid': self.invalid_user_jid,
            'status': 'member'
        }
        resp = self.api.add_members(team_uid, group_jid, data).json()
        assert const.INVALID_DATA == resp['error']
        assert 'Выберите корректный вариант. {jid} нет среди допустимых значений.' \
                   .format(jid=self.invalid_user_jid) == resp['details']['jid']


    @pytest.mark.positive
    def test_get_status_role_owner(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # добавляем участников
        user2_jid = func.add_contact(self.api, team_uid, self.phone2)['jid']
        # создаем группу
        group_jid = func.add_group(self.api, team_uid)['jid']
        resp_cont = func.add_member_to_group(self.api, team_uid, group_jid, user2_jid, 'admin')
        cont_jid = resp_cont['jid']
        resp = self.api.get_member_status(team_uid, group_jid, cont_jid).json()
        assert 'error' not in resp
        assert resp_cont == resp['result']


    @pytest.mark.positive
    @pytest.mark.parametrize("role", [
        'admin',
        'member'
    ])
    def test_get_status_role(self, role):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # добавляем участников
        user2_jid = func.add_contact(self.api, team_uid, self.phone2)['jid']
        user3_jid = func.add_contact(self.api, team_uid, self.phone3)['jid']
        # создаем группу
        group_jid = func.add_group(self.api, team_uid)['jid']
        # добавляем участников в группу
        func.add_member_to_group(self.api, team_uid, group_jid, user2_jid, role)
        resp_cont = func.add_member_to_group(self.api, team_uid, group_jid, user3_jid, 'member')
        user_jid = resp_cont['jid']
        # логинимся участником role и запрашиваем статус
        auth_cookies = auth.login_with_cookies(self.url, self.phone2, self.code2)
        api2 = API(self.url, auth_cookies, is_token_auth=False)
        resp = api2.get_member_status(team_uid, group_jid, user_jid).json()
        assert 'error' not in resp
        assert resp_cont == resp['result']


    @pytest.mark.negative
    def test_get_status_invalid_jid(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # создаем группу
        group_jid = func.add_group(self.api, team_uid)['jid']
        resp = self.api.get_member_status(team_uid, group_jid, self.invalid_user_jid).json()
        assert const.NOT_FOUND == resp['error']


    @pytest.mark.positive
    def test_edit_status_role_owner(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # добавляем участников
        user2_jid = func.add_contact(self.api, team_uid, self.phone2)['jid']
        # создаем группу
        group_jid = func.add_group(self.api, team_uid)['jid']
        resp_cont = func.add_member_to_group(self.api, team_uid, group_jid, user2_jid, 'admin')
        cont_jid = resp_cont['jid']
        status = 'member'
        resp = self.api.edit_member_status(team_uid, group_jid, cont_jid, status).json()
        assert 'error' not in resp
        assert resp_cont['jid'] == resp['result']['jid']
        assert status == resp['result']['status']


    @pytest.mark.positive
    def test_edit_status_role_admin(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # добавляем участников
        user2_jid = func.add_contact(self.api, team_uid, self.phone2)['jid']
        # создаем группу
        group_jid = func.add_group(self.api, team_uid)['jid']
        resp_cont = func.add_member_to_group(self.api, team_uid, group_jid, user2_jid, 'admin')
        cont_jid = resp_cont['jid']
        auth_cookies = auth.login_with_cookies(self.url, self.phone2, self.code2)
        api2 = API(self.url, auth_cookies, is_token_auth=False)
        status = 'member'
        resp = api2.edit_member_status(team_uid, group_jid, cont_jid, status).json()
        assert 'error' not in resp
        assert resp_cont['jid'] == resp['result']['jid']
        assert status == resp['result']['status']


    @pytest.mark.negative
    def test_edit_status_role_member(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # добавляем участников
        user2_jid = func.add_contact(self.api, team_uid, self.phone2)['jid']
        # создаем группу
        group_jid = func.add_group(self.api, team_uid)['jid']
        resp_cont = func.add_member_to_group(self.api, team_uid, group_jid, user2_jid, 'member')
        cont_jid = resp_cont['jid']
        auth_cookies = auth.login_with_cookies(self.url, self.phone2, self.code2)
        api2 = API(self.url, auth_cookies, is_token_auth=False)
        status = 'member'
        resp = api2.edit_member_status(team_uid, group_jid, cont_jid, status).json()
        assert resp['error'] == const.ACCESS_DENIED


    @pytest.mark.negative
    def test_edit_status_invalid_jid(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # создаем группу
        group_jid = func.add_group(self.api, team_uid)['jid']
        resp = self.api.edit_member_status(team_uid, group_jid, self.invalid_user_jid, 'admin').json()
        assert const.NOT_FOUND == resp['error']


    @pytest.mark.positive
    def test_delete_member_role_owner(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # добавляем участников
        user2_jid = func.add_contact(self.api, team_uid, self.phone2)['jid']
        # создаем группу
        group_jid = func.add_group(self.api, team_uid)['jid']
        func.add_member_to_group(self.api, team_uid, group_jid, user2_jid, 'member')
        resp = self.api.delete_member(team_uid, group_jid, user2_jid).json()
        resp2 = self.api.get_group(team_uid, group_jid).json()
        assert 'error' not in resp
        assert {} == resp['result']
        assert not tools.is_items_exist_in_list_of_dict(
            resp2['result']['members'],
            'jid',
            user2_jid)


    @pytest.mark.positive
    def test_delete_member_role_admin(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # добавляем участников
        user2_jid = func.add_contact(self.api, team_uid, self.phone2)['jid']
        user3_jid = func.add_contact(self.api, team_uid, self.phone3)['jid']
        # создаем группу
        group_jid = func.add_group(self.api, team_uid)['jid']
        func.add_member_to_group(self.api, team_uid, group_jid, user2_jid, 'admin')
        func.add_member_to_group(self.api, team_uid, group_jid, user3_jid, 'member')
        auth_cookies = auth.login_with_cookies(self.url, self.phone2, self.code2)
        api2 = API(self.url, auth_cookies, is_token_auth=False)
        resp = api2.delete_member(team_uid, group_jid, user3_jid).json()
        resp2 = api2.get_group(team_uid, group_jid).json()
        assert 'error' not in resp
        assert {} == resp['result']
        assert not tools.is_items_exist_in_list_of_dict(
            resp2['result']['members'],
            'jid',
            user3_jid)


    @pytest.mark.negative
    def test_delete_member_role_member(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # добавляем участников
        user2_jid = func.add_contact(self.api, team_uid, self.phone2)['jid']
        user3_jid = func.add_contact(self.api, team_uid, self.phone3)['jid']
        # создаем группу
        group_jid = func.add_group(self.api, team_uid)['jid']
        func.add_member_to_group(self.api, team_uid, group_jid, user2_jid, 'member')
        func.add_member_to_group(self.api, team_uid, group_jid, user3_jid, 'member')
        auth_cookies = auth.login_with_cookies(self.url, self.phone2, self.code2)
        api2 = API(self.url, auth_cookies, is_token_auth=False)
        resp = api2.delete_member(team_uid, group_jid, user3_jid).json()
        assert resp['error'] == const.ACCESS_DENIED


    @pytest.mark.negative
    def test_delete_member_with_invalid_jid(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # создаем группу
        group_jid = func.add_group(self.api, team_uid)['jid']
        resp = self.api.delete_member(team_uid, group_jid, self.invalid_user_jid).json()
        assert resp['error'] == const.NOT_FOUND


    @pytest.mark.positive
    @pytest.mark.parametrize("filename", [
        'tiger',
        'TIGER.JPEG',
        'tiger.jpg',
        'tiger.PNG'
    ])
    def test_upload_group_icon_valid(self, filename):
        '''
        Пока доступны только PNG и JPG
        'tiger.bmp',
        'tiger.gif',
        'tiger.tiff'
        '''
        group_jid = func.add_group(self.api, self.team_uid)['jid']
        resp = self.api.upload_group_icon(self.team_uid, group_jid, os.path.join(const.TD_FILES, filename)).json()
        assert 'error' not in resp
        assert resp['result']['lg']['url']
        assert resp['result']['sm']['url']


    @pytest.mark.negative
    @pytest.mark.parametrize("filename", [
        'tiger.pdf',
        'tiger.ico'
    ])
    def test_upload_group_icon_invalid(self, filename):
        group_jid = func.add_group(self.api, self.team_uid)['jid']
        resp = self.api.upload_group_icon(self.team_uid, group_jid, os.path.join(const.TD_FILES, filename)).json()
        assert const.INVALID_DATA == resp['error']
        assert 'Ошибка при загрузке. Пожалуйста, попробуйте ещё раз' == resp['details']['file']


    @pytest.mark.positive
    def test_upload_group_icon_admin(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # добавляем участников
        user2_jid = func.add_contact(self.api, team_uid, self.phone2)['jid']
        group_jid = func.add_group(self.api, self.team_uid)['jid']
        # создаем группу
        group_jid = func.add_group(self.api, team_uid)['jid']
        # добавляем участников в группу
        func.add_member_to_group(self.api, team_uid, group_jid, user2_jid, 'admin')
        auth_cookies = auth.login_with_cookies(self.url, self.phone2, self.code2)
        api2 = API(self.url, auth_cookies, is_token_auth=False)
        resp = api2.upload_group_icon(team_uid, group_jid, os.path.join(const.TD_FILES, 'tiger.jpg')).json()
        assert 'error' not in resp
        assert resp['result']['lg']['url']
        assert resp['result']['sm']['url']


    @pytest.mark.negative
    def test_upload_group_icon_member(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # добавляем участников
        user2_jid = func.add_contact(self.api, team_uid, self.phone2)['jid']
        # создаем группу
        group_jid = func.add_group(self.api, team_uid)['jid']
        # добавляем участников в группу
        func.add_member_to_group(self.api, team_uid, group_jid, user2_jid, 'member')
        auth_cookies = auth.login_with_cookies(self.url, self.phone2, self.code2)
        api2 = API(self.url, auth_cookies, is_token_auth=False)
        resp = api2.upload_group_icon(team_uid, group_jid, os.path.join(const.TD_FILES, 'tiger.jpg')).json()
        assert resp['error'] == const.ACCESS_DENIED


    @pytest.mark.positive
    @pytest.mark.parametrize("exist", [
        'icon_exist',
        'icon_not_exist'
    ])
    def test_delete_group_icon(self, exist):
        group_jid = func.add_group(self.api, self.team_uid)['jid']
        if exist == 'icon_exist':
            self.api.upload_group_icon(self.team_uid, group_jid, os.path.join(const.TD_FILES, 'tiger.jpg')).json()
        resp = self.api.delete_group_icon(self.team_uid, group_jid).json()
        assert 'error' not in resp
        assert resp['result']['lg'] is None
        assert resp['result']['sm'] is None


    @pytest.mark.negative
    def test_delete_group_icon_member(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # добавляем участников
        user2_jid = func.add_contact(self.api, team_uid, self.phone2)['jid']
        # создаем группу
        group_jid = func.add_group(self.api, team_uid)['jid']
        # добавляем участников в группу
        func.add_member_to_group(self.api, team_uid, group_jid, user2_jid, 'member')
        auth_cookies = auth.login_with_cookies(self.url, self.phone2, self.code2)
        api2 = API(self.url, auth_cookies, is_token_auth=False)
        resp = api2.delete_group_icon(team_uid, group_jid).json()
        assert resp['error'] == const.ACCESS_DENIED


    @pytest.mark.negative
    def test_delete_group_icon_another_member(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # добавляем участников
        user2_jid = func.add_contact(self.api, team_uid, self.phone2)['jid']
        user3_jid = func.add_contact(self.api, team_uid, self.phone3)['jid']
        # создаем группу
        group_jid = func.add_group(self.api, team_uid)['jid']
        group_jid_2 = func.add_group(self.api, team_uid)['jid']
        # добавляем участников в группу
        func.add_member_to_group(self.api, team_uid, group_jid, user2_jid, 'admin')
        func.add_member_to_group(self.api, team_uid, group_jid_2, user3_jid, 'admin')
        auth_cookies = auth.login_with_cookies(self.url, self.phone2, self.code2)
        api2 = API(self.url, auth_cookies, is_token_auth=False)
        resp = api2.delete_group_icon(team_uid, group_jid_2).json()
        assert resp['error'] == const.ACCESS_DENIED


    @pytest.mark.positive
    def test_get_group_valid_jid(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # добавляем участников
        user2_jid = func.add_contact(self.api, team_uid, self.phone2)['jid']
        # создаем группу
        group_jid = func.add_group(self.api, team_uid)['jid']
        # добавляем участников в группу
        func.add_member_to_group(self.api, team_uid, group_jid, user2_jid, 'admin')
        resp = self.api.get_group(team_uid, group_jid).json()
        assert 'error' not in resp
        assert resp['result']['jid'] == group_jid


    @pytest.mark.negative
    def test_get_group_invalid_jid(self):
        resp = self.api.get_group(self.team_uid, self.invalid_group_jid).json()
        assert resp['error'] == const.NOT_FOUND


    @pytest.mark.positive
    @pytest.mark.parametrize("role", [
        'admin',
        'member'
    ])
    def test_get_group_role(self, role):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # добавляем участников
        user2_jid = func.add_contact(self.api, team_uid, self.phone2)['jid']
        # создаем группу
        group_jid = func.add_group(self.api, team_uid)['jid']
        # добавляем участников в группу
        func.add_member_to_group(self.api, team_uid, group_jid, user2_jid, role)
        auth_cookies = auth.login_with_cookies(self.url, self.phone2, self.code2)
        api2 = API(self.url, auth_cookies, is_token_auth=False)
        resp = api2.get_group(team_uid, group_jid).json()
        assert 'error' not in resp
        assert resp['result']['jid'] == group_jid


    @pytest.mark.negative
    def test_get_group_another_user(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        team_uid_2 = func.add_team(self.api)['uid']
        # добавляем участников
        user2_jid = func.add_contact(self.api, team_uid_2, self.phone2)['jid']
        # создаем группу
        group_jid = func.add_group(self.api, team_uid)['jid']
        group_jid_2 = func.add_group(self.api, team_uid_2)['jid']
        # добавляем участников в группу
        func.add_member_to_group(self.api, team_uid_2, group_jid_2, user2_jid, 'admin')
        auth_cookies = auth.login_with_cookies(self.url, self.phone2, self.code2)
        api2 = API(self.url, auth_cookies, is_token_auth=False)
        resp = api2.get_group(team_uid, group_jid).json()
        assert resp['error'] == const.ACCESS_DENIED


    @pytest.mark.positive
    def test_edit_group_all_params(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # создаем группу
        group_jid = func.add_group(self.api, team_uid)['jid']
        data = {
            'display_name': 'Тестовая группа',
            'description': 'hi',
            'readonly_for_members': True,
            'api_enabled': True,
            'notifications_enabled': True,
            'default_for_all': True,
            'counters_enabled': True,
            'public': True
        }
        resp = self.api.edit_group(team_uid, group_jid, data).json()
        resp = [resp['result']] # преобразования для функции tools.is_items_exist_in_list_of_dict
        for key, value in data.items():
            assert tools.is_items_exist_in_list_of_dict(resp, key, value)


    @pytest.mark.negative
    def test_edit_group_empty_name(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # создаем группу
        group_jid = func.add_group(self.api, team_uid)['jid']
        data = {'display_name': ''}
        resp = self.api.edit_group(team_uid, group_jid, data).json()
        assert const.INVALID_DATA == resp['error']
        assert resp['details']['display_name'] == 'Имя группы не может быть пустым'


    @pytest.mark.positive
    def test_edit_group_role_admin(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # добавляем участников
        user2_jid = func.add_contact(self.api, team_uid, self.phone2)['jid']
        # создаем группу
        group_jid = func.add_group(self.api, team_uid)['jid']
        # добавляем участников в группу
        func.add_member_to_group(self.api, team_uid, group_jid, user2_jid, 'admin')
        auth_cookies = auth.login_with_cookies(self.url, self.phone2, self.code2)
        api2 = API(self.url, auth_cookies, is_token_auth=False)
        data = {'display_name': 'test'}
        resp = api2.edit_group(team_uid, group_jid, data).json()
        assert 'error' not in resp
        assert resp['result']['jid'] == group_jid
        assert resp['result']['display_name'] == data['display_name']


    @pytest.mark.negative
    def test_edit_group_role_member(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # добавляем участников
        user2_jid = func.add_contact(self.api, team_uid, self.phone2)['jid']
        # создаем группу
        group_jid = func.add_group(self.api, team_uid)['jid']
        # добавляем участников в группу
        func.add_member_to_group(self.api, team_uid, group_jid, user2_jid, 'member')
        auth_cookies = auth.login_with_cookies(self.url, self.phone2, self.code2)
        api2 = API(self.url, auth_cookies, is_token_auth=False)
        data = {'display_name': 'test'}
        resp = api2.edit_group(team_uid, group_jid, data).json()
        assert resp['error'] == const.ACCESS_DENIED
        assert resp['details'] == 'Low access level to change group settings'


    @pytest.mark.negative
    def test_edit_group_another_user(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        team_uid_2 = func.add_team(self.api)['uid']
        # добавляем участников
        user2_jid = func.add_contact(self.api, team_uid_2, self.phone2)['jid']
        # создаем группу
        group_jid = func.add_group(self.api, team_uid)['jid']
        group_jid_2 = func.add_group(self.api, team_uid_2)['jid']
        # добавляем участников в группу
        func.add_member_to_group(self.api, team_uid_2, group_jid_2, user2_jid, 'admin')
        auth_cookies = auth.login_with_cookies(self.url, self.phone2, self.code2)
        api2 = API(self.url, auth_cookies, is_token_auth=False)
        data = {'display_name': 'test'}
        resp = api2.edit_group(team_uid, group_jid, data).json()
        assert resp['error'] == const.ACCESS_DENIED


    @pytest.mark.positive
    def test_delete_group_valid_jid(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # создаем группу
        group_jid = func.add_group(self.api, team_uid)['jid']
        resp = self.api.delete_group(team_uid, group_jid).json()
        resp2 = self.api.get_groups(team_uid).json()
        assert 'error' not in resp
        assert resp['result']['jid'] == group_jid
        assert resp['result']['is_archive']
        assert not tools.is_items_exist_in_list_of_dict(
            resp2['result'],
            'jid',
            group_jid)


    @pytest.mark.negative
    def test_delete_group_invalid_jid(self):
        resp = self.api.delete_group(self.team_uid, self.invalid_group_jid).json()
        assert resp['error'] == const.NOT_FOUND


    @pytest.mark.positive
    def test_delete_group_role_admin(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # добавляем участников
        user2_jid = func.add_contact(self.api, team_uid, self.phone2)['jid']
        # создаем группу
        group_jid = func.add_group(self.api, team_uid)['jid']
        # добавляем участников в группу
        func.add_member_to_group(self.api, team_uid, group_jid, user2_jid, 'admin')
        auth_cookies = auth.login_with_cookies(self.url, self.phone2, self.code2)
        api2 = API(self.url, auth_cookies, is_token_auth=False)
        resp = api2.delete_group(team_uid, group_jid).json()
        resp2 = api2.get_groups(team_uid).json()
        assert 'error' not in resp
        assert resp['result']['jid'] == group_jid
        assert resp['result']['is_archive']
        assert not tools.is_items_exist_in_list_of_dict(
            resp2['result'],
            'jid',
            group_jid)


    @pytest.mark.negative
    def test_delete_group_role_member(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # добавляем участников
        user2_jid = func.add_contact(self.api, team_uid, self.phone2)['jid']
        # создаем группу
        group_jid = func.add_group(self.api, team_uid)['jid']
        # добавляем участников в группу
        func.add_member_to_group(self.api, team_uid, group_jid, user2_jid, 'member')
        auth_cookies = auth.login_with_cookies(self.url, self.phone2, self.code2)
        api2 = API(self.url, auth_cookies, is_token_auth=False)
        resp = api2.delete_group(team_uid, group_jid).json()
        assert resp['error'] == const.ACCESS_DENIED


    @pytest.mark.negative
    def test_delete_group_another_user(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # добавляем участников
        user2_jid = func.add_contact(self.api, team_uid, self.phone2)['jid']
        # создаем группу
        group_jid = func.add_group(self.api, team_uid)['jid']
        group_jid_2 = func.add_group(self.api, team_uid)['jid']
        # добавляем участников в группу
        func.add_member_to_group(self.api, team_uid, group_jid_2, user2_jid, 'admin')
        auth_cookies = auth.login_with_cookies(self.url, self.phone2, self.code2)
        api2 = API(self.url, auth_cookies, is_token_auth=False)
        resp = api2.delete_group(team_uid, group_jid).json()
        assert resp['error'] == const.ACCESS_DENIED


    @pytest.mark.positive
    def test_get_public_groups_team_owner(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # добавляем участников
        func.add_contact(self.api, team_uid, self.phone2)['jid']
        # создаем публичную группу новым участником
        auth_cookies = auth.login_with_cookies(self.url, self.phone2, self.code2)
        api2 = API(self.url, auth_cookies, is_token_auth=False)
        group_jid = func.add_group(api2, team_uid, public=True)['jid']
        resp = self.api.get_public_groups(team_uid).json()
        assert 'error' not in resp
        assert resp['result'][0]['jid'] == group_jid
        assert resp['result'][0]['public']


    @pytest.mark.positive
    def test_get_public_groups_team_member(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # добавляем участников
        func.add_contact(self.api, team_uid, self.phone2)['jid']
        # создаем публичную группу
        group_jid = func.add_group(self.api, team_uid, public=True)['jid']
        auth_cookies = auth.login_with_cookies(self.url, self.phone2, self.code2)
        api2 = API(self.url, auth_cookies, is_token_auth=False)
        resp = api2.get_public_groups(team_uid).json()
        assert 'error' not in resp
        assert resp['result'][0]['jid'] == group_jid
        assert resp['result'][0]['public']


    @pytest.mark.positive
    def test_join_to_public_group(self):
        team_info = func.add_team(self.api)
        team_uid = team_info['uid']
        owner_jid = team_info['owner_jid']
        group_info = func.add_group(self.api, team_uid, public=True)
        group_jid = group_info['jid']
        name = group_info['display_name']
        resp = self.api.join_public_group(team_uid, group_jid).json()
        assert 'error' not in resp
        assert resp['result']['display_name'] == name
        assert resp['result']['jid'] == group_jid
        assert tools.is_items_exist_in_list_of_dict(
            resp['result']['members'],
            'jid',
            owner_jid)


    @pytest.mark.negative
    def test_join_to_public_group_user_of_another_team(self):
        # создаем команду
        team_uid_1 = func.add_team(self.api)['uid']
        team_uid_2 = func.add_team(self.api)['uid']
        group_jid_1 = func.add_group(self.api, team_uid_1, public=True)['jid']
        func.add_group(self.api, team_uid_2, public=True)
        resp = self.api.join_public_group(team_uid_2, group_jid_1).json()
        assert const.ACCESS_DENIED == resp['error']
        assert resp['details'] == 'Incorrect data or access level'


    @pytest.mark.negative
    def test_join_to_public_group_invalid_jid(self):
        resp = self.api.join_public_group(self.team_uid, self.invalid_group_jid).json()
        assert resp['error'] == const.NOT_FOUND


    @pytest.mark.positive
    def test_get_roster(self):
        # создаем команду
        team_info = func.add_team(self.api)
        team_uid = team_info['uid']
        user1_jid = team_info['owner_jid']
        # добавляем участников
        user2_jid = func.add_contact(self.api, team_uid, self.phone2)['jid']
        # создаем группу
        private_group_jid = func.add_group(self.api, team_uid)['jid']
        public_group_jid = func.add_group(self.api, team_uid, public=True)['jid']
        resp = self.api.get_roster(team_uid).json()
        keys = ['badge',
                'contacts',
                'devices',
                'direct_chats',
                'groups',
                'sections',
                'tasklists']
        for key in keys:
            assert key in resp['result']
        assert tools.is_items_exist_in_list_of_dict(
            resp['result']['contacts'],
            'jid',
            user1_jid)
        assert tools.is_items_exist_in_list_of_dict(
            resp['result']['contacts'],
            'jid',
            user2_jid)
        assert tools.is_items_exist_in_list_of_dict(
            resp['result']['groups'],
            'jid',
            private_group_jid)
        assert tools.is_items_exist_in_list_of_dict(
            resp['result']['groups'],
            'jid',
            public_group_jid)


    @pytest.mark.negative
    def test_get_roster_invalid_team_uid(self):
        resp = self.api.get_roster(self.invalid_team_uid).json()
        assert resp['error'] == const.NOT_FOUND


    @pytest.mark.positive
    def test_get_chat_admin(self):
        # создаем команду
        team_info = func.add_team(self.api)
        team_uid = team_info['uid']
        # создаем публичную группу
        group_info = func.add_group(self.api, team_uid, public=True)
        group_jid = group_info['jid']
        group_name = group_info['display_name']
        resp = self.api.get_chat(team_uid, group_jid).json()['result']
        assert 'error' not in resp
        assert resp['jid'] == group_jid
        assert resp['display_name'] == group_name


    @pytest.mark.positive
    def test_get_chat_member(self):
        # создаем команду
        team_info = func.add_team(self.api)
        team_uid = team_info['uid']
        # добавляем участников
        user2_jid = func.add_contact(self.api, team_uid, self.phone2)['jid']
        # создаем публичную группу
        group_info = func.add_group(self.api, team_uid, public=True)
        group_jid = group_info['jid']
        group_name = group_info['display_name']
        # добавляем участника в группу
        func.add_member_to_group(self.api, team_uid, group_jid, user2_jid, 'member')
        auth_cookies = auth.login_with_cookies(self.url, self.phone2, self.code2)
        api2 = API(self.url, auth_cookies, is_token_auth=False)
        resp = api2.get_chat(team_uid, group_jid).json()['result']
        assert 'error' not in resp
        assert resp['jid'] == group_jid
        assert resp['display_name'] == group_name


    @pytest.mark.negative
    def test_get_chat_another_user(self):
        # создаем команду
        team_info = func.add_team(self.api)
        team_uid = team_info['uid']
        # добавляем участников
        user2_jid = func.add_contact(self.api, team_uid, self.phone2)['jid']
        # создаем публичную группу
        group_info = func.add_group(self.api, team_uid, public=True)
        group_jid = group_info['jid']
        auth_cookies = auth.login_with_cookies(self.url, self.phone2, self.code2)
        api2 = API(self.url, auth_cookies, is_token_auth=False)
        resp = api2.get_chat(team_uid, group_jid).json()
        assert resp['error'] == const.ACCESS_DENIED


    @pytest.mark.negative
    def test_get_chat_invalid_jid(self):
        resp = self.api.get_chat(self.team_uid, self.invalid_user_jid).json()
        assert resp['error'] == const.NOT_FOUND


    @pytest.mark.positive
    def test_delete_chat_admin(self):
        # создаем команду
        team_info = func.add_team(self.api)
        team_uid = team_info['uid']
        # создаем публичную группу
        group_info = func.add_group(self.api, team_uid, public=True)
        group_jid = group_info['jid']
        group_name = group_info['display_name']
        resp = self.api.delete_chat(team_uid, group_jid).json()['result']
        assert 'error' not in resp
        assert resp['jid'] == group_jid
        assert resp['display_name'] == group_name
        assert resp['hidden']


    @pytest.mark.negative
    def test_delete_chat_invalid_jid(self):
        resp = self.api.get_chat(self.team_uid, self.invalid_group_jid).json()
        assert resp['error'] == const.NOT_FOUND


    @pytest.mark.positive
    def test_delete_chat_member(self):
        # создаем команду
        team_info = func.add_team(self.api)
        team_uid = team_info['uid']
        # добавляем участников
        user2_jid = func.add_contact(self.api, team_uid, self.phone2)['jid']
        # создаем публичную группу
        group_info = func.add_group(self.api, team_uid, public=True)
        group_jid = group_info['jid']
        group_name = group_info['display_name']
        # добавляем участника в группу
        func.add_member_to_group(self.api, team_uid, group_jid, user2_jid, 'member')
        auth_cookies = auth.login_with_cookies(self.url, self.phone2, self.code2)
        api2 = API(self.url, auth_cookies, is_token_auth=False)
        resp = api2.delete_chat(team_uid, group_jid).json()['result']
        assert 'error' not in resp
        assert resp['jid'] == group_jid
        assert resp['display_name'] == group_name
        assert resp['hidden']


    @pytest.mark.negative
    def test_delete_chat_another_user(self):
        # создаем команду
        team_info = func.add_team(self.api)
        team_uid = team_info['uid']
        # добавляем участников
        user2_jid = func.add_contact(self.api, team_uid, self.phone2)['jid']
        # создаем публичную группу
        group_info = func.add_group(self.api, team_uid, public=True)
        group_jid = group_info['jid']
        auth_cookies = auth.login_with_cookies(self.url, self.phone2, self.code2)
        api2 = API(self.url, auth_cookies, is_token_auth=False)
        resp = api2.delete_chat(team_uid, group_jid).json()
        assert resp['error'] == const.ACCESS_DENIED

