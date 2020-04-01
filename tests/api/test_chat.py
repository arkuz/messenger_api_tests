import pytest
import os
import uuid
import datetime

from helpers.api import API
from helpers.readers import read_yaml, read_json
import helpers.const as const
import helpers.auth as auth
import helpers.tools as tools
import helpers.functions as func


class TestsChat:
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
    def test_get_botcommands_admin(self):
        team_uid = func.add_team(self.api)['uid']
        group_jid = func.add_group(self.api, team_uid)['jid']
        resp = self.api.get_botcommands(team_uid, group_jid).json()
        path = os.path.join(const.EXPECTED_RESULTS, 'bot_commands_admin.json')
        expected = read_json(path)
        assert 'error' not in resp
        assert resp['result'] == expected['result']


    @pytest.mark.positive
    def test_get_botcommands_member(self):
        team_uid = func.add_team(self.api)['uid']
        group_jid = func.add_group(self.api, team_uid)['jid']
        user2_jid = func.add_contact(self.api, team_uid, self.phone2)['jid']
        func.add_member_to_group(self.api, team_uid, group_jid, user2_jid, 'member')
        api2 = auth.login_another_user(self.url, self.phone2, self.code2)
        resp = api2.get_botcommands(team_uid, group_jid).json()
        path = os.path.join(const.EXPECTED_RESULTS, 'bot_commands_member.json')
        expected = read_json(path)
        assert 'error' not in resp
        assert resp['result'] == expected['result']


    @pytest.mark.positive
    def test_linkscheck_dog(self):
        team_uid = func.add_team(self.api)['uid']
        group_jid = func.add_group(self.api, team_uid)['jid']
        dog = '@все'
        text = f'{dog} , привет!'
        resp = self.api.linkscheck(team_uid, group_jid, text).json()
        expected = {
            'pattern': dog,
            'text': dog,
            'url': f'otv://{group_jid}'
        }
        assert 'error' not in resp
        assert resp['result']['links'][0] == expected


    @pytest.mark.positive
    def test_linkscheck_sharp(self):
        team_uid = func.add_team(self.api)['uid']
        group = func.add_group(self.api, team_uid)
        group_jid = group['jid']
        group_name = group['display_name']
        text = f'#{group_name}'
        resp = self.api.linkscheck(team_uid, group_jid, text).json()
        expected = {
            'pattern': text,
            'text': text,
            'url': f'otv://{group_jid}'
        }
        assert 'error' not in resp
        assert resp['result']['links'][0] == expected


    @pytest.mark.positive
    def test_linkscheck_https(self):
        team_uid = func.add_team(self.api)['uid']
        group_jid = func.add_group(self.api, team_uid)['jid']
        text = 'https://www.google.ru/'
        resp = self.api.linkscheck(team_uid, group_jid, text).json()
        assert 'error' not in resp
        resp = resp['result']['links'][0]
        assert resp['pattern'] == text
        assert resp['preview']['title'] == 'Google'
        assert resp['text'] == text
        assert resp['url'] == text


    @pytest.mark.positive
    def test_linkscheck_http(self):
        team_uid = func.add_team(self.api)['uid']
        group_jid = func.add_group(self.api, team_uid)['jid']
        text = 'http://www.yandex.ru/'
        resp = self.api.linkscheck(team_uid, group_jid, text).json()
        assert 'error' not in resp
        resp = resp['result']['links'][0]
        assert resp['pattern'] == text
        assert resp['preview']['title'] == 'Яндекс'
        assert resp['text'] == text
        assert resp['url'] == text


    @pytest.mark.positive
    def test_linkscheck_rus(self):
        team_uid = func.add_team(self.api)['uid']
        group_jid = func.add_group(self.api, team_uid)['jid']
        text = 'http://кто.рф/'
        resp = self.api.linkscheck(team_uid, group_jid, text).json()
        assert 'error' not in resp
        resp = resp['result']['links'][0]
        assert resp['pattern'] == text
        assert resp['preview']['title'] == '.РФ - наш домен'
        assert resp['text'] == text
        assert resp['url'] == 'http://xn--j1ail.xn--p1ai/'


    @pytest.mark.negative
    def test_linkscheck_without_link(self):
        team_uid = func.add_team(self.api)['uid']
        group_jid = func.add_group(self.api, team_uid)['jid']
        text = 'Привет, как дела? !;%:?*()_ How are you'
        resp = self.api.linkscheck(team_uid, group_jid, text).json()
        assert 'error' not in resp
        assert not resp['result']['links']


    @pytest.mark.negative
    def test_send_text_invalid_team_uid(self):
        team_uid = func.add_team(self.api)['uid']
        group_jid = func.add_group(self.api, team_uid)['jid']
        data = {'text': tools.generate_random_string()}
        resp = self.api.send_msg_text(self.invalid_team_uid, group_jid, data).json()
        assert resp['error'] == const.NOT_FOUND


    @pytest.mark.negative
    def test_send_text_invalid_group_jid(self):
        data = {'text': tools.generate_random_string()}
        resp = self.api.send_msg_text(self.team_uid, self.invalid_group_jid, data).json()
        assert resp['error'] == const.NOT_FOUND


    @pytest.mark.positive
    def test_send_text_all_symbols(self):
        # создаем группу
        group_jid = func.add_group(self.api, self.team_uid)['jid']
        data = {'text': '1234\ndgJFОРПорп !@ #$% ^&* ()'}
        resp = self.api.send_msg_text(self.team_uid, group_jid, data).json()
        assert 'error' not in resp['result']
        assert resp['result']['content']['text'] == data['text']


    @pytest.mark.positive
    def test_send_text_8000_symbols(self):
        # создаем группу
        group_jid = func.add_group(self.api, self.team_uid)['jid']
        data = {'text': tools.generate_random_string(8001)}
        resp = self.api.send_msg_text(self.team_uid, group_jid, data).json()
        assert 'error' not in resp['result']
        assert resp['result']['content']['text'] == data['text']


    @pytest.mark.negative
    def test_send_text_8001_symbols(self):
        # создаем группу
        group_jid = func.add_group(self.api, self.team_uid)['jid']
        data = {'text': tools.generate_random_string(8002)}
        resp = self.api.send_msg_text(self.team_uid, group_jid, data).json()
        assert resp['error'] == const.INVALID_DATA
        assert resp['details']['text'] == 'Ошибка отправки'


    @pytest.mark.positive
    def test_send_text_with_message_id(self):
        # создаем группу
        group_jid = func.add_group(self.api, self.team_uid)['jid']
        message_id = str(uuid.uuid4())
        data = {
            'text': 'hello',
            'message_id': message_id,
        }
        resp = self.api.send_msg_text(self.team_uid, group_jid, data).json()
        assert 'error' not in resp
        assert resp['result']['message_id'] == message_id


    @pytest.mark.positive
    def test_send_text_with_nopreview(self):
        # создаем группу
        group_jid = func.add_group(self.api, self.team_uid)['jid']
        data = {
            'text': 'https://github.com/arkuz',
            'nopreview': True,
        }
        resp = self.api.send_msg_text(self.team_uid, group_jid, data).json()
        assert 'error' not in resp
        assert not resp['result']['links']


    @pytest.mark.negative
    def test_send_empty_text(self):
        # создаем группу
        group_jid = func.add_group(self.api, self.team_uid)['jid']
        data = {'text': ''}
        resp = self.api.send_msg_text(self.team_uid, group_jid, data).json()
        assert resp['error'] == const.INVALID_DATA


    @pytest.mark.positive
    def test_send_text_readonly_for_members_false(self):
        # создаем группу с  с readonly_for_members: false
        data = {'display_name': tools.generate_random_string(),
                'public': False,
                'readonly_for_members': False}
        resp = self.api.add_group(self.team_uid, data).json()
        group_jid = resp['result']['jid']
        # добавляем участника в команду и в группу
        user2_jid = func.add_contact(self.api, self.team_uid, self.phone2)['jid']
        func.add_member_to_group(self.api, self.team_uid, group_jid, user2_jid, 'member')
        auth_cookies = auth.login_with_cookies(self.url, self.phone2, self.code2)
        api2 = API(self.url, auth_cookies, is_token_auth=False)
        msg_data = {'text': tools.generate_random_string()}
        resp = api2.send_msg_text(self.team_uid, group_jid, msg_data).json()
        assert 'error' not in resp
        assert resp['result']['content']['text'] == msg_data['text']


    @pytest.mark.negative
    def test_send_text_readonly_for_members_true(self):
        # создаем группу с readonly_for_members: true
        data = {'display_name': tools.generate_random_string(),
                'public': False,
                'readonly_for_members': True}
        resp = self.api.add_group(self.team_uid, data).json()
        group_jid = resp['result']['jid']
        # добавляем участника в команду и в группу
        user2_jid = func.add_contact(self.api, self.team_uid, self.phone2)['jid']
        func.add_member_to_group(self.api, self.team_uid, group_jid, user2_jid, 'member')
        auth_cookies = auth.login_with_cookies(self.url, self.phone2, self.code2)
        api2 = API(self.url, auth_cookies, is_token_auth=False)
        msg_data = {'text': tools.generate_random_string()}
        resp = api2.send_msg_text(self.team_uid, group_jid, msg_data).json()
        assert resp['error'] == const.ACCESS_DENIED


    @pytest.mark.positive
    @pytest.mark.parametrize("filename", [
        'tiger.pdf',
        'word.docx',
        'excel.xlsx',
        'tiger.gif',
        'tiger.PNG',
        'tiger',
        'tiger.bmp',
        'audio.wav'
    ])
    def test_send_file(self, filename):
        resp = self.api.send_msg_file(self.team_uid, self.group_jid, os.path.join(const.TD_FILES, filename)).json()
        assert 'error' not in resp['result']
        assert resp['result']['content']['name'] == filename


    @pytest.mark.positive
    @pytest.mark.parametrize("filename", [
        'audio.wav',
        'audio.m4a',
        'audio.mp3'
    ])
    def test_send_audio(self, filename):
        resp = self.api.send_msg_audio(self.team_uid, self.group_jid, os.path.join(const.TD_FILES, filename)).json()
        assert 'error' not in resp['result']
        assert '.mp3' in resp['result']['content']['mediaURL']
        assert resp['result']['content']['type'] == 'audiomsg'


    @pytest.mark.negative
    @pytest.mark.parametrize("filename", [
        'tiger.pdf',
        'word.docx',
        'excel.xlsx'
    ])
    def test_send_audio_invalid(self, filename):
        resp = self.api.send_msg_audio(self.team_uid, self.group_jid, os.path.join(const.TD_FILES, filename)).json()
        assert resp['error'] == const.INVALID_DATA
        assert 'Ошибка при загрузке. Проверьте тип файла и попробуйте ещё раз. Mime type is' in resp['details']['file']


    # тесты на галерею


    @pytest.mark.positive
    def test_get_messages(self):
        group_jid = func.add_group(self.api, self.team_uid)['jid']
        # добавляем сообщения в цикле
        exp_msg = {}
        for i in range(5):
            # эта магия с i для того, чтобы ключи словаря exp_msg совпадали с ключами в resp т.к. в ответе есть всегда 2 дефолтных сообщения
            i = i + 2
            text = 'msg_{}_{}'.format(tools.generate_random_string(7), i)
            exp_msg[i] = text
            func.send_text(self.api, self.team_uid, group_jid, text)
        resp = self.api.get_messages(self.team_uid, group_jid).json()
        assert 'error' not in resp['result']
        assert len(resp['result']['messages']) == 7
        num = 6
        while num > 1:
            assert resp['result']['messages'][num]['content']['text'] == exp_msg[num]
            num = num - 1


    @pytest.mark.negative
    def test_get_messages_invalid_team_uid(self):
        resp = self.api.get_messages(self.invalid_team_uid, self.group_jid).json()
        assert resp['error'] == const.NOT_FOUND


    @pytest.mark.negative
    def test_get_messages_invalid_chat_jid(self):
        resp = self.api.get_messages(self.team_uid, self.invalid_group_jid).json()
        assert resp['error'] == const.NOT_FOUND


    @pytest.mark.positive
    def test_get_messages_old_from(self):
        group_jid = func.add_group(self.api, self.team_uid)['jid']
        msg_list = []
        # добавляем сообщения в цикле
        for i in range(3):
            text = 'msg_{}_{}'.format(tools.generate_random_string(7), i)
            msg_list.append(func.send_text(self.api, self.team_uid, group_jid, text)['message_id'])
        params = {'old_from': msg_list[-1]}
        resp = self.api.get_messages(self.team_uid, group_jid, params).json()
        assert 'error' not in resp
        assert tools.is_items_exist_in_list_of_dict(
            resp['result']['messages'], 'message_id', msg_list[0])
        assert tools.is_items_exist_in_list_of_dict(
            resp['result']['messages'], 'message_id', msg_list[1])
        assert not tools.is_items_exist_in_list_of_dict(
            resp['result']['messages'], 'message_id', msg_list[-1])


    @pytest.mark.positive
    def test_get_messages_new_from(self):
        group_jid = func.add_group(self.api, self.team_uid)['jid']
        msg_list = []
        # добавляем сообщения в цикле
        for i in range(3):
            text = 'msg_{}_{}'.format(tools.generate_random_string(7), i)
            msg_list.append(func.send_text(self.api, self.team_uid, group_jid, text)['message_id'])
        params = {'new_from': msg_list[0]}
        resp = self.api.get_messages(self.team_uid, group_jid, params).json()
        assert 'error' not in resp
        assert len(resp['result']['messages']) == 2
        assert tools.is_items_exist_in_list_of_dict(
            resp['result']['messages'], 'message_id', msg_list[1])
        assert tools.is_items_exist_in_list_of_dict(
            resp['result']['messages'], 'message_id', msg_list[-1])
        assert not tools.is_items_exist_in_list_of_dict(
            resp['result']['messages'], 'message_id', msg_list[0])


    @pytest.mark.positive
    def test_get_messages_limit(self):
        group_jid = func.add_group(self.api, self.team_uid)['jid']
        # добавляем сообщения в цикле
        for i in range(5):
            text = 'msg_{}_{}'.format(tools.generate_random_string(7), i)
            func.send_text(self.api, self.team_uid, group_jid, text)
        limit = 3
        params = {'limit': limit}
        resp = self.api.get_messages(self.team_uid, group_jid, params).json()
        assert 'error' not in resp['result']
        assert len(resp['result']['messages']) == limit


    @pytest.mark.positive
    def test_get_messages_exact(self):
        group_jid = func.add_group(self.api, self.team_uid)['jid']
        text = tools.generate_random_string(7)
        message_id = func.send_text(self.api, self.team_uid, group_jid, text)['message_id']
        params = {'exact': message_id}
        resp = self.api.get_messages(self.team_uid, group_jid, params).json()
        assert 'error' not in resp['result']
        assert len(resp['result']['messages']) == 1
        assert resp['result']['messages'][0]['content']['text'] == text


    @pytest.mark.positive
    def test_get_messages_unread(self):
        user2_jid = func.add_contact(self.api, self.team_uid, self.phone2)['jid']
        group_jid = func.add_group(self.api, self.team_uid)['jid']
        func.add_member_to_group(self.api, self.team_uid, group_jid, user2_jid, 'admin')
        # добавляем сообщения в цикле
        exp_msg = {}
        for i in range(5):
            # эта магия с i для того, чтобы ключи словаря exp_msg совпадали с ключами в resp т.к. в ответе есть всегда 2 дефолтных сообщения
            i = i + 1
            text = 'msg_{}_{}'.format(tools.generate_random_string(7), i)
            exp_msg[i] = text
            func.send_text(self.api, self.team_uid, group_jid, text)
        auth_cookies = auth.login_with_cookies(self.url, self.phone2, self.code2)
        api2 = API(self.url, auth_cookies, is_token_auth=False)
        params = {'unread': True}
        resp = api2.get_messages(self.team_uid, group_jid, params).json()
        assert 'error' not in resp['result']
        assert len(resp['result']['messages']) == 6
        num = 5
        while num > 0:
            assert resp['result']['messages'][num]['content']['text'] == exp_msg[num]
            num = num - 1


    @pytest.mark.positive
    def test_get_filtered_messages(self):
        team_uid = func.add_team(self.api)['uid']
        group_jid = func.add_group(self.api, team_uid)['jid']
        # добавляем сообщения в цикле
        exp_msg = {}
        count = 5
        for i in range(count):
            # эта магия с i для того, чтобы ключи словаря exp_msg совпадали с ключами в resp т.к. в ответе есть всегда 2 дефолтных сообщения
            i = count - 1
            text = 'msg_{}_{}'.format(tools.generate_random_string(7), i)
            exp_msg[i] = text
            func.send_text(self.api, team_uid, group_jid, text)
        resp = self.api.get_filtered_messages(team_uid).json()
        assert 'error' not in resp['result']
        assert len(resp['result']['objects']) == 7
        num = count
        while num < count:
            assert resp['result']['objects'][num]['content']['text'] == exp_msg[num]
            num = num + 1


    @pytest.mark.negative
    def test_get_filtered_messages_invalid_team_uid(self):
        resp = self.api.get_filtered_messages(self.invalid_team_uid).json()
        assert resp['error'] == const.NOT_FOUND


    @pytest.mark.positive
    def test_get_filtered_messages_limit_offset(self):
        group_jid = func.add_group(self.api, self.team_uid)['jid']
        exp_text = ''
        for i in range(5):
            text = 'msg_{}_{}'.format(tools.generate_random_string(7), i)
            func.send_text(self.api, self.team_uid, group_jid, text)
            # запоминаем текст сообщения
            if i == 0:
                exp_text = text
        params = {
            'limit': 1,
            'offset': 4,
        }
        resp = self.api.get_filtered_messages(self.team_uid, params).json()
        assert 'error' not in resp['result']
        assert len(resp['result']['objects']) == 1
        assert resp['result']['objects'][0]['content']['text'] == exp_text


    @pytest.mark.positive
    def test_get_messages_chat(self):
        group_jid = func.add_group(self.api, self.team_uid)['jid']
        group_jid_2 = func.add_group(self.api, self.team_uid)['jid']
        group_jid_3 = func.add_group(self.api, self.team_uid)['jid']
        # добавляем сообщения
        text = 'msg_{}'.format(tools.generate_random_string(7))
        func.send_text(self.api, self.team_uid, group_jid, text)
        func.send_text(self.api, self.team_uid, group_jid_2, text)
        func.send_text(self.api, self.team_uid, group_jid_3, text)
        params = {
            'chat': f'{group_jid},{group_jid_2}',
        }
        resp = self.api.get_filtered_messages(self.team_uid, params).json()
        assert 'error' not in resp
        assert tools.is_items_exist_in_list_of_dict(
            resp['result']['objects'],
            'chat',
            group_jid,
        )
        assert tools.is_items_exist_in_list_of_dict(
            resp['result']['objects'],
            'chat',
            group_jid_2,
        )
        assert not tools.is_items_exist_in_list_of_dict(
            resp['result']['objects'],
            'chat',
            group_jid_3,
        )


    @pytest.mark.positive
    def test_get_messages_sender(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # приглашаем пользователей
        user1_jid = func.get_my_jid(self.api, team_uid)
        user2_jid = func.add_contact(self.api, team_uid, self.phone2)['jid']
        user3_jid = func.add_contact(self.api, team_uid, self.phone3)['jid']
        # добавляем участников к группе
        group_jid = func.add_group(self.api, team_uid)['jid']
        func.add_member_to_group(self.api, team_uid, group_jid, user2_jid, 'member')
        func.add_member_to_group(self.api, team_uid, group_jid, user3_jid, 'admin')
        # добавляем сообщения
        api2 = auth.login_another_user(self.url, self.phone2, self.code2)
        api3 = auth.login_another_user(self.url, self.phone3, self.code3)
        text = 'msg_{}'.format(tools.generate_random_string(7))
        func.send_text(self.api, team_uid, group_jid, text)
        func.send_text(api2, team_uid, group_jid, text)
        func.send_text(api3, team_uid, group_jid, text)
        params = {
            'sender': f'{user1_jid},{user2_jid}',
        }
        resp = self.api.get_filtered_messages(team_uid, params).json()
        assert 'error' not in resp
        assert tools.is_items_exist_in_list_of_dict(
            resp['result']['objects'],
            'from',
            user1_jid,
        )
        assert tools.is_items_exist_in_list_of_dict(
            resp['result']['objects'],
            'from',
            user2_jid,
        )
        assert not tools.is_items_exist_in_list_of_dict(
            resp['result']['objects'],
            'from',
            user3_jid,
        )


    @pytest.mark.positive
    def test_get_messages_text(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # приглашаем пользователей
        user1_jid = func.get_my_jid(self.api, team_uid)
        user2_jid = func.add_contact(self.api, team_uid, self.phone2)['jid']
        user3_jid = func.add_contact(self.api, team_uid, self.phone3)['jid']
        # добавляем участников к группе
        group_jid = func.add_group(self.api, team_uid)['jid']
        func.add_member_to_group(self.api, team_uid, group_jid, user2_jid, 'member')
        func.add_member_to_group(self.api, team_uid, group_jid, user3_jid, 'admin')
        # добавляем сообщения
        api2 = auth.login_another_user(self.url, self.phone2, self.code2)
        api3 = auth.login_another_user(self.url, self.phone3, self.code3)
        pattern = 'msg'
        text = f'{pattern}_{tools.generate_random_string(7)}'
        msg1 = f'1_{text}'
        msg2 = f'2_{text}'
        msg3 = 'hello'
        func.send_text(self.api, team_uid, group_jid, msg1)
        func.send_text(api2, team_uid, group_jid, msg2)
        func.send_text(api3, team_uid, group_jid, msg3)
        params = {
            'text': pattern,
        }
        resp = self.api.get_filtered_messages(team_uid, params).json()
        assert 'error' not in resp
        assert len(resp['result']['objects']) == 2
        assert resp['result']['objects'][0]['content']['text'] == msg2
        assert resp['result']['objects'][1]['content']['text'] == msg1


    @pytest.mark.positive
    @pytest.mark.parametrize("type,text_filename", [
        ('plain', 'hello'),
        ('image', 'tiger.PNG'),
        ('video', 'video.mp4'),
        ('file', 'word.docx'),
    ])
    def test_get_messages_type(self, type, text_filename):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # приглашаем пользователей
        group_jid = func.add_group(self.api, team_uid)['jid']
        # добавляем сообщения
        func.send_text(self.api, team_uid, group_jid, 'hello')
        self.api.send_msg_file(team_uid, group_jid, os.path.join(const.TD_FILES, 'tiger.PNG'))
        self.api.send_msg_file(team_uid, group_jid, os.path.join(const.TD_FILES, 'video.mp4'))
        self.api.send_msg_file(team_uid, group_jid, os.path.join(const.TD_FILES, 'word.docx'))
        params = {
            'type': type,
        }
        resp = self.api.get_filtered_messages(team_uid, params).json()
        assert 'error' not in resp
        assert len(resp['result']['objects']) == 1
        if type == 'plain':
            assert resp['result']['objects'][0]['content']['text'] == text_filename
        else:
            assert resp['result']['objects'][0]['content']['name'] == text_filename


    @pytest.mark.skip
    @pytest.mark.positive
    def test_get_messages_important(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        group_jid = func.add_group(self.api, team_uid)['jid']
        func.send_text(self.api, team_uid, group_jid, 'hello')
        msg_data = {'text': 'important_message',
                    'important': True}
        #msg_data = json.dumps(msg_data)
        resp = self.api.send_msg_text(team_uid, group_jid, msg_data).json()
        tools.print_formatted_json(resp, ensure_ascii=False)
        params = {
            'important': 'true',
        }
        resp = self.api.get_filtered_messages(team_uid, params).json()
        tools.print_formatted_json(resp, ensure_ascii=False)
        assert 'error' not in resp
        assert len(resp['result']['objects']) == 1
        assert resp['result']['objects'][0]['important']


    @pytest.mark.positive
    def test_get_messages_chat_type(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # приглашаем пользователей
        user2_jid = func.add_contact(self.api, team_uid, self.phone2)['jid']
        # добавляем участников к группе
        group_jid = func.add_group(self.api, team_uid)['jid']
        func.add_member_to_group(self.api, team_uid, group_jid, user2_jid, 'member')
        # добавляем сообщения
        pattern = 'msg'
        text = f'{pattern}_{tools.generate_random_string(7)}'
        msg1 = f'1_{text}'
        msg2 = f'2_{text}'
        func.send_text(self.api, team_uid, group_jid, msg1)
        func.send_text(self.api, team_uid, user2_jid, msg2)
        params = {
            'chat_type': 'direct',
        }
        resp = self.api.get_filtered_messages(team_uid, params).json()
        assert 'error' not in resp
        assert len(resp['result']['objects']) == 1
        assert resp['result']['objects'][0]['chat_type'] == 'direct'
        assert resp['result']['objects'][0]['content']['text'] == msg2


    @pytest.mark.positive
    def test_get_messages_date_from_future(self):
        date_from = datetime.datetime.now() + datetime.timedelta(days=1)
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # добавляем участников к группе
        group_jid = func.add_group(self.api, team_uid)['jid']
        # добавляем сообщения
        text = f'msg_{tools.generate_random_string(7)}'
        func.send_text(self.api, team_uid, group_jid, text)
        params = {
            'date_from': date_from,
        }
        resp = self.api.get_filtered_messages(team_uid, params).json()
        assert 'error' not in resp
        assert not resp['result']['objects']


    @pytest.mark.positive
    def test_get_messages_date_to_past(self):
        date_to = datetime.datetime.now() + datetime.timedelta(days=-1)
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # добавляем участников к группе
        group_jid = func.add_group(self.api, team_uid)['jid']
        # добавляем сообщения
        text = f'msg_{tools.generate_random_string(7)}'
        func.send_text(self.api, team_uid, group_jid, text)
        params = {
            'date_to': date_to,
        }
        resp = self.api.get_filtered_messages(team_uid, params).json()
        assert 'error' not in resp
        assert not resp['result']['objects']

