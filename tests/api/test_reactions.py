import pytest
import os
import json
import logging

from helpers.api import API
from helpers.readers import read_yaml, read_json
import helpers.const as const
import helpers.auth as auth
import helpers.tools as tools
import helpers.functions as func


class TestsReactions:
    #logging.basicConfig(level=logging.DEBUG)

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
    invalid_message_id = '00000000-0000-0000-0000-982d4bac29a3'

    reaction1 = '😀'
    reaction2 = '😽'
    reaction3 = '✋'


    def setup_class(self):
        # Логин и создание команды, далее эта команда используется в тестах
        self.url = self.config['api']['url']
        phone = self.user['phone']
        code = self.user['code']
        auth_cookies = auth.login_with_cookies(self.url, phone, code)
        self.api = API(self.url, auth_cookies, is_token_auth=False)
        resp = func.add_team(self.api)
        self.team_uid = resp['uid']
        resp = func.add_group(self.api, self.team_uid)
        self.group_jid = resp['jid']


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
    def test_get_all_exist_reactions(self):
        resp = self.api.get_all_exist_reactions().json()
        path = os.path.join(const.EXPECTED_RESULTS, 'reactions.json')
        expected = read_json(path)
        assert 'error' not in resp
        assert resp['result'] == expected['result']


    @pytest.mark.positive
    def test_add_reaction_owner(self):
        owner_jid = func.get_my_jid(self.api, self.team_uid)
        text = f'Hello, my friend {tools.generate_random_string()}'
        message_id = func.send_text(self.api, self.team_uid, self.group_jid, text=text)['message_id']
        resp = self.api.add_edit_reaction(self.team_uid, message_id, self.reaction1).json()
        assert 'error' not in resp
        assert resp['result']['name'] == self.reaction1
        assert resp['result']['sender'] == owner_jid


    @pytest.mark.negative
    def test_add_invalid_reaction(self):
        text = f'Hello, my friend {tools.generate_random_string()}'
        message_id = func.send_text(self.api, self.team_uid, self.group_jid, text=text)['message_id']
        resp = self.api.add_edit_reaction(self.team_uid, message_id, ':-)').json()
        assert resp['error'] == const.NOT_FOUND


    @pytest.mark.positive
    def test_add_reaction_member(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # добавляем участника
        member_jid = func.add_contact(self.api, team_uid, self.phone2)['jid']
        # добавляем гуппу
        group_jid = func.add_group(self.api, team_uid)['jid']
        # добавляем участника к группе
        func.add_member_to_group(self.api, team_uid, group_jid, member_jid, 'member')
        text = f'Hello, my friend {tools.generate_random_string()}'
        message_id = func.send_text(self.api, team_uid, group_jid, text=text)['message_id']
        api2 = auth.login_another_user(self.url, self.phone2, self.code2)
        resp = api2.add_edit_reaction(team_uid, message_id, self.reaction1).json()
        assert 'error' not in resp
        assert resp['result']['name'] == self.reaction1
        assert resp['result']['sender'] == member_jid


    @pytest.mark.skip 
    @pytest.mark.positive
    def test_add_reaction_member_without_group(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # добавляем участника
        member_jid = func.add_contact(self.api, team_uid, self.phone2)['jid']
        # добавляем гуппу
        group_jid = func.add_group(self.api, team_uid)['jid']
        # добавляем участника к группе
        #func.add_member_to_group(self.api, team_uid, group_jid, member_jid, 'member')
        text = f'Hello, my friend {tools.generate_random_string()}'
        message_id = func.send_text(self.api, team_uid, group_jid, text=text)['message_id']
        api2 = auth.login_another_user(self.url, self.phone2, self.code2)
        resp = api2.add_edit_reaction(team_uid, message_id, self.reaction1).json()
        tools.print_formatted_json(resp, ensure_ascii=False)
        # ACCESS DENIED должно быть
        assert 'error' not in resp
        assert resp['result']['name'] == self.reaction1
        assert resp['result']['sender'] == member_jid


    @pytest.mark.positive
    def test_edit_reaction_owner(self):
        owner_jid = func.get_my_jid(self.api, self.team_uid)
        text = f'Hello, my friend {tools.generate_random_string()}'
        message_id = func.send_text(self.api, self.team_uid, self.group_jid, text=text)['message_id']
        resp = self.api.add_edit_reaction(self.team_uid, message_id, self.reaction1).json()
        resp_edit = self.api.add_edit_reaction(self.team_uid, message_id, self.reaction2).json()
        assert resp['result']['name'] == self.reaction1
        assert 'error' not in resp_edit
        assert resp_edit['result']['name'] == self.reaction2
        assert resp_edit['result']['sender'] == owner_jid


    @pytest.mark.positive
    def test_edit_reaction_member(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # добавляем участника
        member_jid = func.add_contact(self.api, team_uid, self.phone2)['jid']
        # добавляем гуппу
        group_jid = func.add_group(self.api, team_uid)['jid']
        # добавляем участника к группе
        func.add_member_to_group(self.api, team_uid, group_jid, member_jid, 'member')
        text = f'Hello, my friend {tools.generate_random_string()}'
        message_id = func.send_text(self.api, team_uid, group_jid, text=text)['message_id']
        api2 = auth.login_another_user(self.url, self.phone2, self.code2)
        resp = api2.add_edit_reaction(team_uid, message_id, self.reaction1).json()
        resp_edit = api2.add_edit_reaction(team_uid, message_id, self.reaction2).json()
        assert resp['result']['name'] == self.reaction1
        assert 'error' not in resp_edit
        assert resp_edit['result']['name'] == self.reaction2
        assert resp_edit['result']['sender'] == member_jid


    @pytest.mark.positive
    def test_get_reaction_on_message_owner(self):
        owner_jid = func.get_my_jid(self.api, self.team_uid)
        text = f'Hello, my friend {tools.generate_random_string()}'
        message_id = func.send_text(self.api, self.team_uid, self.group_jid, text=text)['message_id']
        self.api.add_edit_reaction(self.team_uid, message_id, self.reaction1).json()
        resp = self.api.get_my_reaction_by_name(self.team_uid, message_id, self.reaction1).json()
        assert 'error' not in resp
        assert resp['result']['name'] == self.reaction1
        assert resp['result']['sender'] == owner_jid


    @pytest.mark.negative
    def test_get_reaction_on_message_owner_not_exist_reaction(self):
        text = f'Hello, my friend {tools.generate_random_string()}'
        message_id = func.send_text(self.api, self.team_uid, self.group_jid, text=text)['message_id']
        self.api.add_edit_reaction(self.team_uid, message_id, self.reaction1).json()
        resp = self.api.get_my_reaction_by_name(self.team_uid, message_id, self.reaction3).json()
        assert resp['error'] == const.NOT_FOUND


    @pytest.mark.positive
    def test_delete_reaction_owner(self):
        text = f'Hello, my friend {tools.generate_random_string()}'
        message_id = func.send_text(self.api, self.team_uid, self.group_jid, text=text)['message_id']
        self.api.add_edit_reaction(self.team_uid, message_id, self.reaction1).json()
        resp = self.api.delete_my_reaction(self.team_uid, message_id, self.reaction1).json()
        resp2 = self.api.get_my_reactions_on_message(self.team_uid, message_id).json()
        assert 'error' not in resp
        assert resp['result'] is None
        assert not resp2['result']


    @pytest.mark.negative
    def test_delete_reaction_owner_message_without_reactions(self):
        text = f'Hello, my friend {tools.generate_random_string()}'
        message_id = func.send_text(self.api, self.team_uid, self.group_jid, text=text)['message_id']
        resp = self.api.delete_my_reaction(self.team_uid, message_id, self.reaction3).json()
        assert 'error' not in resp
        assert resp['result'] is None


    @pytest.mark.positive
    def test_delete_reaction_member(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # добавляем участника
        member_jid = func.add_contact(self.api, team_uid, self.phone2)['jid']
        # добавляем гуппу
        group_jid = func.add_group(self.api, team_uid)['jid']
        # добавляем участника к группе
        func.add_member_to_group(self.api, team_uid, group_jid, member_jid, 'member')
        text = f'Hello, my friend {tools.generate_random_string()}'
        message_id = func.send_text(self.api, team_uid, group_jid, text=text)['message_id']
        api2 = auth.login_another_user(self.url, self.phone2, self.code2)
        api2.add_edit_reaction(team_uid, message_id, self.reaction1).json()
        resp = api2.delete_my_reaction(team_uid, message_id, self.reaction1).json()
        resp2 = api2.get_my_reactions_on_message(team_uid, message_id).json()
        assert 'error' not in resp
        assert resp['result'] is None
        assert not resp2['result']


    @pytest.mark.positive
    def test_get_all_my_reactions_owner(self):
        owner_jid = func.get_my_jid(self.api, self.team_uid)
        reactions = [
            self.reaction1,
            self.reaction2,
            self.reaction3
        ]
        text = f'Hello, my friend {tools.generate_random_string()}'
        message_id = func.send_text(self.api, self.team_uid, self.group_jid, text=text)['message_id']
        for reaction in reactions:
            self.api.add_edit_reaction(self.team_uid, message_id, reaction).json()
        resp = self.api.get_my_reactions_on_message(self.team_uid, message_id).json()
        assert 'error' not in resp
        for reaction in reactions:
            assert tools.is_items_exist_in_list_of_dict(
                resp['result'],
                'name',
                reaction
            )
        for item in resp['result']:
            assert item['sender'] == owner_jid


    @pytest.mark.positive
    def test_get_all_my_reactions_member(self):
        reactions = [
            self.reaction1,
            self.reaction2,
            self.reaction3
        ]
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # добавляем участника
        member_jid = func.add_contact(self.api, team_uid, self.phone2)['jid']
        # добавляем гуппу
        group_jid = func.add_group(self.api, team_uid)['jid']
        # добавляем участника к группе
        func.add_member_to_group(self.api, team_uid, group_jid, member_jid, 'member')
        text = f'Hello, my friend {tools.generate_random_string()}'
        api2 = auth.login_another_user(self.url, self.phone2, self.code2)
        message_id = func.send_text(api2, team_uid, group_jid, text=text)['message_id']
        for reaction in reactions:
            api2.add_edit_reaction(team_uid, message_id, reaction).json()
        resp = api2.get_my_reactions_on_message(team_uid, message_id).json()
        assert 'error' not in resp
        for reaction in reactions:
            assert tools.is_items_exist_in_list_of_dict(
                resp['result'],
                'name',
                reaction
            )
        for item in resp['result']:
            assert item['sender'] == member_jid

