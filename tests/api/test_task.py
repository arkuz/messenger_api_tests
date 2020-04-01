import pytest
import os
import json
import datetime

from helpers.api import API
from helpers.readers import read_yaml
import helpers.const as const
import helpers.auth as auth
import helpers.tools as tools
import helpers.functions as func


class TestsTask:
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
    invalid_tasklist_uid = '00000000-0000-0000-0000-a5c63104318c'
    invalid_observer_jid = '00000000-0000-0000-0000-fd2527b63770@task'
    invalid_point_uid = '00000000-0000-0000-0000-a5c63104318c'


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
    def test_add_tasklist_with_empty_name(self):
        data = {'name': ''}
        resp = self.api.add_tasklist(self.team_uid, data).json()
        assert const.INVALID_DATA == resp['error']
        assert 'Обязательное поле.' == resp['details']['name']


    @pytest.mark.positive
    @pytest.mark.parametrize("first_symbol", [
        '1','@','#','_ _','а','Я'
    ])
    def test_add_tasklist_with_name_start_with(self, first_symbol):
        name = first_symbol + tools.generate_random_string(30)
        data = {'name': name}
        resp = self.api.add_tasklist(self.team_uid, data).json()
        assert 'error' not in resp
        assert tools.is_items_exist_in_list_of_dict(
            resp['result'],
            'name',
            name
        )


    @pytest.mark.positive
    def test_add_tasklist_with_name_one_symbol(self):
        name = tools.generate_random_string(2)
        data = {'name': name}
        resp = self.api.add_tasklist(self.team_uid, data).json()
        assert 'error' not in resp
        assert tools.is_items_exist_in_list_of_dict(
            resp['result'],
            'name',
            name
        )


    @pytest.mark.positive
    def test_add_tasklist_with_name_200_symbols(self):
        name = tools.generate_random_string(201)
        data = {'name': name}
        resp = self.api.add_tasklist(self.team_uid, data).json()
        assert 'error' not in resp
        assert tools.is_items_exist_in_list_of_dict(
            resp['result'],
            'name',
            name
        )


    @pytest.mark.positive
    def test_add_tasklist_member_invalid(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # добавляем участников
        func.add_contact(self.api, team_uid, self.phone2)
        auth_cookies = auth.login_with_cookies(self.url, self.phone2, self.code2)
        api2 = API(self.url, auth_cookies, is_token_auth=False)
        data = {'name': tools.generate_random_string()}
        resp = api2.add_tasklist(self.team_uid, data).json()
        assert resp['error'] == const.ACCESS_DENIED


    @pytest.mark.negative
    def test_add_team_with_name_201_symbols(self):
        data = {'name': tools.generate_random_string(202)}
        resp = self.api.add_tasklist(self.team_uid, data).json()
        assert const.INVALID_DATA == resp['error']
        assert 'Убедитесь, что это значение содержит не более 200 символов (сейчас 201).' == resp['details']['name']


    @pytest.mark.negative
    @pytest.mark.parametrize("move", [
        'move_after',
        'move_before'
    ])
    def test_add_tasklist_move_after_before_invalid(self, move):
        data = {'name': 'hello',
                move: self.invalid_tasklist_uid}
        resp = self.api.add_tasklist(self.team_uid, data).json()
        assert const.INVALID_DATA == resp['error']
        assert 'Список задач не найден' == resp['details'][move]


    @pytest.mark.positive
    def test_add_tasklist_move_after(self):
        resp = self.api.get_tasklists(self.team_uid).json()
        after_uid = resp['result'][-1]['uid']
        name = 'after_' + tools.generate_random_string(10)
        data = {'name': name,
                'move_after': after_uid}
        resp = self.api.add_tasklist(self.team_uid, data).json()
        current_uid = resp['result'][-1]['uid']
        resp = self.api.get_tasklists(self.team_uid).json()
        assert 'error' not in resp
        assert resp['result'][-2]['uid'] == after_uid
        assert resp['result'][-1]['uid'] == current_uid


    @pytest.mark.positive
    def test_add_tasklist_move_before(self):
        resp = self.api.get_tasklists(self.team_uid).json()
        after_uid = resp['result'][0]['uid']
        name = 'before_' + tools.generate_random_string(10)
        data = {'name': name,
                'move_before': after_uid}
        resp = self.api.add_tasklist(self.team_uid, data).json()
        current_uid = resp['result'][0]['uid']
        resp = self.api.get_tasklists(self.team_uid).json()
        assert 'error' not in resp
        assert resp['result'][1]['uid'] == after_uid
        assert resp['result'][0]['uid'] == current_uid


    @pytest.mark.positive
    def test_get_tasklists(self):
        resp = self.api.get_tasklists(self.team_uid).json()
        assert 'error' not in resp
        for item in resp['result']:
            assert 'name' in item
            assert 'uid' in item


    @pytest.mark.positive
    def test_get_tasklists_member_team(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # добавляем участников
        func.add_contact(self.api, team_uid, self.phone2)
        auth_cookies = auth.login_with_cookies(self.url, self.phone2, self.code2)
        api2 = API(self.url, auth_cookies, is_token_auth=False)
        resp = api2.get_tasklists(team_uid).json()
        assert 'error' not in resp
        for item in resp['result']:
            assert 'name' in item
            assert 'uid' in item


    @pytest.mark.negative
    def test_get_tasklists_outsider(self):
        api2 = auth.login_another_user(self.url, self.phone4, self.code4)
        resp = api2.get_tasklists(self.team_uid).json()
        assert resp['error'] == const.ACCESS_DENIED


    @pytest.mark.negative
    @pytest.mark.parametrize("move", [
        'move_after',
        'move_before'
    ])
    def test_move_tasklist_invalid(self, move):
        tasklist_uid = func.add_tasklist(self.api, self.team_uid)['uid']
        if move == 'move_after':
            resp = self.api.set_tasklist_move_after(self.team_uid,
                                                   self.invalid_tasklist_uid,
                                                   tasklist_uid)
        else:
            resp = self.api.set_tasklist_move_before(self.team_uid,
                                                     tasklist_uid,
                                                     self.invalid_tasklist_uid)
        resp = resp.json()
        assert resp['error'] == const.ACCESS_DENIED
        assert 'tasklist "{uid}" not found'.format(uid=self.invalid_tasklist_uid) == resp['details']


    @pytest.mark.positive
    def test_move_tasklist_move_after(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # получаем список тасклистов и запоминаем uid последнего
        resp = self.api.get_tasklists(team_uid).json()
        after_uid = resp['result'][-1]['uid']
        # создаем новый тасклист и запоминаем его uid
        name = 'after_' + tools.generate_random_string(10)
        resp = func.add_tasklist(self.api, team_uid, name)
        current_uid = resp['uid']
        # ставим тасклист current_uid после after_uid
        self.api.set_tasklist_move_after(team_uid, current_uid, after_uid)
        # получаем список тасклистов для проверки
        resp = self.api.get_tasklists(team_uid).json()
        assert 'error' not in resp
        assert resp['result'][-2]['uid'] == after_uid
        assert resp['result'][-1]['uid'] == current_uid


    @pytest.mark.positive
    def test_move_tasklist_move_before(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # получаем список тасклистов и запоминаем uid первого
        resp = self.api.get_tasklists(team_uid).json()
        before_uid = resp['result'][0]['uid']
        # создаем новый тасклист и запоминаем его uid
        name = 'before_' + tools.generate_random_string(10)
        resp = func.add_tasklist(self.api, team_uid, name)
        current_uid = resp['uid']
        # ставим тасклист current_uid перед after_uid
        self.api.set_tasklist_move_before(team_uid, current_uid, before_uid)
        # получаем список тасклистов для проверки
        resp = self.api.get_tasklists(team_uid).json()
        assert 'error' not in resp
        assert resp['result'][1]['uid'] == before_uid
        assert resp['result'][0]['uid'] == current_uid


    @pytest.mark.positive
    def test_move_tasklist_move_before_member_invalid(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # добавляем участников
        func.add_contact(self.api, team_uid, self.phone2)
        # получаем список тасклистов и запоминаем uid первого
        resp = self.api.get_tasklists(team_uid).json()
        before_uid = resp['result'][0]['uid']
        # создаем новый тасклист и запоминаем его uid
        name = 'before_' + tools.generate_random_string(10)
        resp = func.add_tasklist(self.api, team_uid, name)
        current_uid = resp['uid']
        # ставим тасклист current_uid перед after_uid
        auth_cookies = auth.login_with_cookies(self.url, self.phone2, self.code2)
        api2 = API(self.url, auth_cookies, is_token_auth=False)
        resp = api2.set_tasklist_move_before(team_uid, current_uid, before_uid).json()
        assert resp['error'] == const.ACCESS_DENIED


    @pytest.mark.positive
    def test_get_tasklist(self):
        tasklist_uid = func.add_tasklist(self.api, self.team_uid)['uid']
        resp = self.api.get_tasklist(self.team_uid, tasklist_uid).json()
        assert 'error' not in resp
        assert resp['result']['uid'] == tasklist_uid


    @pytest.mark.negative
    def test_get_tasklist_invalid_uid(self):
        resp = self.api.get_tasklist(self.team_uid, self.invalid_tasklist_uid).json()
        assert resp['error'] == const.ACCESS_DENIED
        assert 'tasklist "{uid}" not found'.format(uid=self.invalid_tasklist_uid) == resp['details']


    @pytest.mark.positive
    def test_get_tasklist_member_team(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # добавляем участников
        func.add_contact(self.api, team_uid, self.phone2)
        # создаем тасклист
        tasklist_uid = func.add_tasklist(self.api, team_uid)['uid']
        auth_cookies = auth.login_with_cookies(self.url, self.phone2, self.code2)
        api2 = API(self.url, auth_cookies, is_token_auth=False)
        resp = api2.get_tasklist(team_uid, tasklist_uid).json()
        assert 'error' not in resp
        assert resp['result']['uid'] == tasklist_uid


    @pytest.mark.negative
    def test_get_tasklist_outsider(self):
        tasklist_uid = func.add_tasklist(self.api, self.team_uid)['uid']
        api2 = auth.login_another_user(self.url, self.phone4, self.code4)
        resp = api2.get_tasklist(self.team_uid, tasklist_uid).json()
        assert resp['error'] == const.ACCESS_DENIED


    @pytest.mark.negative
    def test_edit_tasklist_invalid_uid(self):
        resp = self.api.edit_tasklist(self.team_uid, self.invalid_tasklist_uid, 'hello').json()
        assert resp['error'] == const.ACCESS_DENIED
        assert 'tasklist "{uid}" not found'.format(uid=self.invalid_tasklist_uid) == resp['details']


    @pytest.mark.positive
    def test_edit_tasklist(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # создаем тасклист
        tasklist_uid = func.add_tasklist(self.api, team_uid)['uid']
        name = 'edit_' + tools.generate_random_string()
        resp = self.api.edit_tasklist(team_uid, tasklist_uid, name).json()
        assert 'error' not in resp
        assert resp['result']['uid'] == tasklist_uid
        assert resp['result']['name'] == name


    @pytest.mark.positive
    def test_edit_tasklist_admin(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # добавляем участников
        func.add_contact(self.api, team_uid, self.phone2, 'admin')
        # создаем тасклист
        tasklist_uid = func.add_tasklist(self.api, team_uid)['uid']
        name = 'edit_' + tools.generate_random_string()
        api2 = auth.login_another_user(self.url, self.phone2, self.code2)
        resp = api2.edit_tasklist(team_uid, tasklist_uid, name).json()
        assert 'error' not in resp
        assert resp['result']['uid'] == tasklist_uid
        assert resp['result']['name'] == name


    @pytest.mark.negative
    def test_edit_tasklist_member(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # добавляем участников
        func.add_contact(self.api, team_uid, self.phone2, 'member')
        # создаем тасклист
        tasklist_uid = func.add_tasklist(self.api, team_uid)['uid']
        name = 'edit_' + tools.generate_random_string()
        api2 = auth.login_another_user(self.url, self.phone2, self.code2)
        resp = api2.edit_tasklist(team_uid, tasklist_uid, name).json()
        assert resp['error'] == const.ACCESS_DENIED


    @pytest.mark.negative
    def test_edit_tasklist_outsider(self):
        tasklist_uid = func.add_tasklist(self.api, self.team_uid)['uid']
        api2 = auth.login_another_user(self.url, self.phone4, self.code4)
        resp = api2.edit_tasklist(self.team_uid, tasklist_uid, 'hello').json()
        assert resp['error'] == const.ACCESS_DENIED


    @pytest.mark.positive
    def test_delete_tasklist(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # создаем тасклист
        tasklist_uid = func.add_tasklist(self.api, team_uid)['uid']
        resp = self.api.delete_tasklist(team_uid, tasklist_uid).json()
        resp2 = self.api.get_tasklists(team_uid).json()
        assert 'error' not in resp
        assert resp['result'] is None
        assert not tools.is_items_exist_in_list_of_dict(
            resp2['result'],
            'uid',
            tasklist_uid
        )


    @pytest.mark.negative
    def test_delete_tasklist_invalid_uid(self):
        resp = self.api.delete_tasklist(self.team_uid, self.invalid_tasklist_uid).json()
        assert resp['error'] == const.ACCESS_DENIED
        assert 'tasklist "{uid}" not found'.format(uid=self.invalid_tasklist_uid) == resp['details']


    @pytest.mark.negative
    def test_delete_tasklist_member(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # добавляем участников
        func.add_contact(self.api, team_uid, self.phone2, 'member')
        # создаем тасклист
        tasklist_uid = func.add_tasklist(self.api, team_uid)['uid']
        api2 = auth.login_another_user(self.url, self.phone2, self.code2)
        resp = api2.delete_tasklist(team_uid, tasklist_uid).json()
        assert resp['error'] == const.ACCESS_DENIED


    @pytest.mark.negative
    def test_delete_tasklist_outsider(self):
        tasklist_uid = func.add_tasklist(self.api, self.team_uid)['uid']
        api2 = auth.login_another_user(self.url, self.phone4, self.code4)
        resp = api2.delete_tasklist(self.team_uid, tasklist_uid).json()
        assert resp['error'] == const.ACCESS_DENIED


    @pytest.mark.positive
    def test_force_delete_tasklist(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # создаем тасклист
        tasklist_uid = func.add_tasklist(self.api, team_uid)['uid']
        resp = self.api.force_delete_tasklist(team_uid, tasklist_uid).json()
        resp2 = self.api.get_tasklists(team_uid).json()
        assert 'error' not in resp
        assert resp['result'] is None
        assert not tools.is_items_exist_in_list_of_dict(
            resp2['result'],
            'uid',
            tasklist_uid
        )


    @pytest.mark.negative
    def test_force_delete_tasklist_invalid_uid(self):
        resp = self.api.force_delete_tasklist(self.team_uid, self.invalid_tasklist_uid).json()
        assert resp['error'] == const.ACCESS_DENIED
        assert 'tasklist "{uid}" not found'.format(uid=self.invalid_tasklist_uid) == resp['details']


    @pytest.mark.negative
    def test_force_delete_tasklist_member(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # добавляем участников
        func.add_contact(self.api, team_uid, self.phone2, 'member')
        # создаем тасклист
        tasklist_uid = func.add_tasklist(self.api, team_uid)['uid']
        api2 = auth.login_another_user(self.url, self.phone2, self.code2)
        resp = api2.force_delete_tasklist(team_uid, tasklist_uid).json()
        assert resp['error'] == const.ACCESS_DENIED


    @pytest.mark.negative
    def test_force_delete_tasklist_outsider(self):
        tasklist_uid = func.add_tasklist(self.api, self.team_uid)['uid']
        api2 = auth.login_another_user(self.url, self.phone4, self.code4)
        resp = api2.force_delete_tasklist(self.team_uid, tasklist_uid).json()
        assert resp['error'] == const.ACCESS_DENIED


    @pytest.mark.positive
    def test_force_delete_tasklist_with_task_different_user(self):
        # создаем команду
        team_uid = func.add_team(self.api, 'my_team_555')['uid']
        observer_jid = func.get_my_jid(self.api, team_uid)
        # добавляем пользователя
        func.add_contact(self.api, team_uid, self.phone2, role='admin')['jid']
        # создаем тасклист
        tasklist_uid = func.add_tasklist(self.api, team_uid, 'my_tasklist')['uid']
        # создаем задачу пользователем 1 в новом тасклисте
        task_user1_uid = func.add_task(self.api, team_uid, title='task_user1', tasklist=tasklist_uid)['uid']
        # создаем задачу пользователем 2 в новом тасклисте и в обсерверы назначаем первого пользователя (для удобства отладки)
        api2 = auth.login_another_user(self.url, self.phone2, self.code2)
        data = {
            'title': 'task_user2',
            'observers': [observer_jid],
            'tasklist': tasklist_uid,
        }
        data = json.dumps(data)
        task_user2_uid = api2.add_task(team_uid, data).json()['result']['uid']
        # принудительно удаляем тасклист
        resp = self.api.force_delete_tasklist(team_uid, tasklist_uid).json()
        # получаем все тасклисты
        resp2 = self.api.get_tasklists(team_uid).json()
        # получаем uid тасклта по умолчанию, задачи переместлись в него
        changed_tasklist_uid = resp2['result'][-1]['uid']
        # получаем список задач из тасклта по умолчанию
        params = {'tasklist': changed_tasklist_uid}
        resp3 = self.api.get_tasks(team_uid, params).json()
        assert 'error' not in resp
        assert resp['result'] is None
        assert not tools.is_items_exist_in_list_of_dict(
            resp2['result'],
            'uid',
            tasklist_uid
        )
        assert tools.is_items_exist_in_list_of_dict(
            resp3['result']['objects'],
            'uid',
            task_user1_uid
        )
        assert tools.is_items_exist_in_list_of_dict(
            resp3['result']['objects'],
            'uid',
            task_user2_uid
        )


    @pytest.mark.positive
    def test_add_task_empty_params(self):
        owner_jid = self.api.get_contacts(self.team_uid).json()['result'][0]['jid']
        data = {}
        resp = self.api.add_task(self.team_uid, data).json()
        assert not 'error' in resp
        resp = resp['result']
        assert resp['owner'] == owner_jid
        assert resp['num'] == 1
        assert not resp['observers']
        assert not resp['tags']
        assert resp['task_status'] == 'new'
        assert resp['jid']
        assert resp['uid']
        assert resp['tasklist']


    @pytest.mark.negative
    def test_add_task_invalid_tasklist_uid(self):
        data = {'tasklist': self.invalid_tasklist_uid}
        resp = self.api.add_task(self.team_uid, data).json()
        assert resp['error'] == const.INVALID_DATA
        assert "Некорректный список задач: '{uid}' Tasklist matching query does not exist.".format(
            uid=self.invalid_tasklist_uid) == resp['details']['tasklist']


    @pytest.mark.positive
    def test_add_task_many_params(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # добавляем участников
        observer_jid = func.add_contact(self.api, team_uid, self.phone2)['jid']
        owner_jid = func.get_my_jid(self.api, team_uid)
        deadline = tools.get_datetime_iso_string(datetime.datetime.now() + datetime.timedelta(days=5))
        remind_at = tools.get_datetime_iso_string(datetime.datetime.now() + datetime.timedelta(days=4))
        title = 'Первая строчка становится названием задачи'
        description = f'{title}\nОстальное уже описание. Assignee не обязателен.'
        message = func.send_text(self.api, team_uid, observer_jid)
        message_id = message['message_id']
        message_text = message['text']
        data = {
            "assignee": owner_jid,
            "deadline": deadline,
            "description": description,
            "linked_messages": [
                message_id
            ],
            "observers": [
                observer_jid
            ],
            "remind_at": remind_at,
            "tags": [
                'архиважно'
            ]
        }
        data = json.dumps(data)
        resp = self.api.add_task(team_uid, data).json()['result']
        assert not 'error' in resp
        assert resp['title'] == title
        assert resp['assignee'] == owner_jid
        assert resp['deadline'] == deadline
        assert resp['description'] == description
        assert resp['linked_messages'][0]['content']['text'] == message_text
        assert resp['observers'][0] == observer_jid
        assert resp['tags'][0] == 'архиважно'


    @pytest.mark.positive
    @pytest.mark.parametrize('role',[
        'admin',
        'member'
    ])
    def test_add_task_role(self, role):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # добавляем участников
        func.add_contact(self.api, team_uid, self.phone2, role)
        # создаем задачу
        api2 = auth.login_another_user(self.url, self.phone2, self.code2)
        task = func.add_task(api2, team_uid)
        resp = api2.get_tasks(team_uid).json()
        assert 'error' not in resp
        assert tools.is_items_exist_in_list_of_dict(
            resp['result']['objects'],
            'uid',
            task['uid']
        )


    @pytest.mark.negative
    def test_add_task_insider(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        api4 = auth.login_another_user(self.url, self.phone4, self.code4)
        resp = api4.add_task(team_uid).json()
        assert resp['error'] == const.ACCESS_DENIED


    @pytest.mark.positive
    @pytest.mark.parametrize('task_status',[
        'new',
        'done'
    ])
    def test_get_tasks_task_status(self, task_status):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # создаем задачу
        data = {'task_status': task_status}
        task_uid = self.api.add_task(team_uid, data).json()['result']['uid']
        params = {'task_status': task_status}
        resp = self.api.get_tasks(team_uid, params).json()
        assert not 'error' in resp
        assert len(resp['result']['objects']) == 1
        assert resp['result']['objects'][0]['uid'] == task_uid


    @pytest.mark.positive
    def test_get_tasks_tasklist(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # создаем тасклист
        tasklist_uid = func.add_tasklist(self.api, team_uid)['uid']
        # создаем задачу
        data = {'tasklist': tasklist_uid}
        task_uid = self.api.add_task(team_uid, data).json()['result']['uid']
        params = {'tasklist': tasklist_uid}
        resp = self.api.get_tasks(team_uid, params).json()
        assert 'error' not in resp
        assert len(resp['result']['objects']) == 1
        assert resp['result']['objects'][0]['tasklist'] == tasklist_uid
        assert resp['result']['objects'][0]['uid'] == task_uid


    @pytest.mark.skip
    @pytest.mark.positive
    @pytest.mark.parametrize('tags, tags_param',[
        (['mark1'], 'mark1'),
        (['mark2'], 'mark2'),
        (['mark1', 'mark2'], 'mark1,mark2')

    ])
    def test_get_tasks_tags(self, tags, tags_param):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # создаем задачу
        data = {'tags': tags}
        data = json.dumps(data)
        task_uid = self.api.add_task(team_uid, data).json()['result']['uid']
        params = {'tags': tags_param}
        resp = self.api.get_tasks(team_uid, params).json()
        tools.print_formatted_json(resp, ensure_ascii=False)
        assert 'error' not in resp
        assert len(resp['result']['objects']) == 1
        assert resp['result']['objects'][0]['tags'] == tags
        assert resp['result']['objects'][0]['uid'] == task_uid


    @pytest.mark.positive
    def test_get_tasks_num(self):
        num = 1
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # создаем задачи
        task_uid = self.api.add_task(team_uid).json()['result']['uid']
        params = {'num': num}
        resp = self.api.get_tasks(team_uid, params).json()
        assert 'error' not in resp
        assert len(resp['result']['objects']) == 1
        assert resp['result']['objects'][0]['num'] == num
        assert resp['result']['objects'][0]['uid'] == task_uid


    @pytest.mark.positive
    def test_get_tasks_q_title(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # создаем задачу
        title = 'hello555'
        data = {'title': title}
        task_uid = self.api.add_task(team_uid, data).json()['result']['uid']
        params = {'q': title}
        resp = self.api.get_tasks(team_uid, params).json()
        assert 'error' not in resp
        assert len(resp['result']['objects']) == 1
        assert resp['result']['objects'][0]['title'] == title
        assert resp['result']['objects'][0]['uid'] == task_uid


    @pytest.mark.positive
    def test_get_tasks_q_description(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # создаем задачу
        description = 'description555'
        data = {'description': description}
        task_uid = self.api.add_task(team_uid, data).json()['result']['uid']
        params = {'q': description}
        resp = self.api.get_tasks(team_uid, params).json()
        assert 'error' not in resp
        assert len(resp['result']['objects']) == 1
        assert resp['result']['objects'][0]['description'] == description
        assert resp['result']['objects'][0]['uid'] == task_uid


    @pytest.mark.positive
    def test_get_tasks_owner(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # создаем задачу
        task_uid = self.api.add_task(team_uid).json()['result']['uid']
        owner_jid = func.get_my_jid(self.api, team_uid)
        params = {'owner': owner_jid}
        resp = self.api.get_tasks(team_uid, params).json()
        assert 'error' not in resp
        assert len(resp['result']['objects']) == 1
        assert resp['result']['objects'][0]['owner'] == owner_jid
        assert resp['result']['objects'][0]['uid'] == task_uid


    @pytest.mark.positive
    def test_get_tasks_observers(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # добавляем участника
        observer_jid = func.add_contact(self.api, team_uid, self.phone2)['jid']
        # создаем задачу
        data = {'observers': [observer_jid]}
        data = json.dumps(data)
        task_uid = self.api.add_task(team_uid, data).json()['result']['uid']
        params = {'observers': observer_jid}
        resp = self.api.get_tasks(team_uid, params=params).json()
        assert 'error' not in resp
        assert len(resp['result']['objects']) == 1
        assert resp['result']['objects'][0]['observers'][0] == observer_jid
        assert resp['result']['objects'][0]['uid'] == task_uid


    @pytest.mark.positive
    def test_get_tasks_member(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        owner_jid = func.get_my_jid(self.api, team_uid)
        # добавляем участника
        observer_jid = func.add_contact(self.api, team_uid, self.phone2)['jid']
        # создаем задачу
        data = {'observers': [observer_jid]}
        data = json.dumps(data)
        task_uid = self.api.add_task(team_uid, data).json()['result']['uid']
        params = {'member': observer_jid}
        resp = self.api.get_tasks(team_uid, params=params).json()
        assert 'error' not in resp
        assert len(resp['result']['objects']) == 1
        assert resp['result']['objects'][0]['owner'] == owner_jid
        assert resp['result']['objects'][0]['observers'][0] == observer_jid
        assert resp['result']['objects'][0]['uid'] == task_uid


    @pytest.mark.positive
    def test_get_tasks_limit(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # создаем задачу
        self.api.add_task(team_uid).json()['result']['uid']
        task_uid_2 = self.api.add_task(team_uid).json()['result']['uid']
        params = {'limit': 1}
        resp = self.api.get_tasks(team_uid, params).json()
        assert 'error' not in resp
        assert len(resp['result']['objects']) == 1
        assert resp['result']['objects'][0]['uid'] == task_uid_2


    @pytest.mark.positive
    def test_get_tasks_offset(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # создаем задачу
        task_uid = self.api.add_task(team_uid).json()['result']['uid']
        self.api.add_task(team_uid).json()['result']['uid']
        params = {'offset': 1}
        resp = self.api.get_tasks(team_uid, params).json()
        assert 'error' not in resp
        assert len(resp['result']['objects']) == 1
        assert resp['result']['objects'][0]['uid'] == task_uid


    @pytest.mark.positive
    def test_add_observer_admin(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # добавляем участника
        observer_jid = func.add_contact(self.api, team_uid, self.phone2)['jid']
        # создаем задачу
        task_jid = self.api.add_task(team_uid).json()['result']['jid']
        self.api.add_observer(team_uid, task_jid, observer_jid).json()
        resp = self.api.get_tasks(team_uid).json()
        assert 'error' not in resp
        assert len(resp['result']['objects']) == 1
        assert resp['result']['objects'][0]['jid'] == task_jid
        assert resp['result']['objects'][0]['observers'][0] == observer_jid


    @pytest.mark.negative
    def test_add_observer_outsider(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # создаем задачу
        task_jid = self.api.add_task(team_uid).json()['result']['jid']
        api2 = auth.login_another_user(self.url, self.phone4, self.code4)
        resp = api2.add_observer(team_uid, task_jid, self.invalid_observer_jid).json()


    @pytest.mark.negative
    def test_add_observer_invalid_observer_jid(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # создаем задачу
        task_jid = self.api.add_task(team_uid).json()['result']['jid']
        resp = self.api.add_observer(team_uid, task_jid, self.invalid_observer_jid).json()
        assert const.INVALID_DATA == resp['error']
        assert f'Некорректный ID участника: {self.invalid_observer_jid}' == resp['details']['jid']


    @pytest.mark.positive
    def test_get_observers_admin(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # добавляем участника
        observer_jid = func.add_contact(self.api, team_uid, self.phone2)['jid']
        # создаем задачу
        task_jid = self.api.add_task(team_uid).json()['result']['jid']
        self.api.add_observer(team_uid, task_jid, observer_jid)
        resp = self.api.get_observers(team_uid, task_jid).json()
        assert 'error' not in resp
        assert len(resp['result']) == 1
        assert resp['result'][0] == observer_jid


    @pytest.mark.positive
    def test_delete_observers_admin(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # добавляем участника
        observer_jid = func.add_contact(self.api, team_uid, self.phone2)['jid']
        # создаем задачу
        task_jid = self.api.add_task(team_uid).json()['result']['jid']
        self.api.add_observer(team_uid, task_jid, observer_jid)
        resp = self.api.get_observers(team_uid, task_jid).json()
        resp1 = self.api.delete_observer(team_uid, task_jid, observer_jid).json()
        assert resp['result'][0] == observer_jid
        assert 'error' not in resp1
        assert not resp1['result']


    @pytest.mark.positive
    def test_delete_observers_member(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # добавляем участника
        observer_jid = func.add_contact(self.api, team_uid, self.phone2, 'member')['jid']
        # создаем задачу
        task_jid = self.api.add_task(team_uid).json()['result']['jid']
        self.api.add_observer(team_uid, task_jid, observer_jid)
        resp = self.api.get_observers(team_uid, task_jid).json()
        api2 = auth.login_another_user(self.url, self.phone2, self.code2)
        resp1 = api2.delete_observer(team_uid, task_jid, observer_jid).json()
        assert resp['result'][0] == observer_jid
        assert 'error' not in resp1
        assert not resp1['result']


    @pytest.mark.negative
    def test_delete_observers_outsider(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # добавляем участника
        observer_jid = func.add_contact(self.api, team_uid, self.phone2, 'member')['jid']
        # создаем задачу
        task_jid = self.api.add_task(team_uid).json()['result']['jid']
        self.api.add_observer(team_uid, task_jid, observer_jid)
        resp = self.api.get_observers(team_uid, task_jid).json()
        api2 = auth.login_another_user(self.url, self.phone4, self.code4)
        resp1 = api2.delete_observer(team_uid, task_jid, observer_jid).json()
        assert resp['result'][0] == observer_jid
        assert resp1['error'] == const.ACCESS_DENIED


    @pytest.mark.positive
    def test_get_task_admin(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # создаем задачу
        task_jid = self.api.add_task(team_uid).json()['result']['jid']
        resp = self.api.get_task(team_uid, task_jid).json()
        assert 'error' not in resp
        assert resp['result']['jid'] == task_jid


    @pytest.mark.positive
    def test_get_task_role_member_observer(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # добавляем участника
        observer_jid = func.add_contact(self.api, team_uid, self.phone2, 'member')['jid']
        # создаем задачу
        task_jid = self.api.add_task(team_uid).json()['result']['jid']
        self.api.add_observer(team_uid, task_jid, observer_jid)
        api2 = auth.login_another_user(self.url, self.phone2, self.code2)
        resp = api2.get_task(team_uid, task_jid).json()
        assert 'error' not in resp
        assert resp['result']['jid'] == task_jid


    @pytest.mark.negative
    def test_get_task_role_admin_not_observer(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # добавляем участника
        observer_jid = func.add_contact(self.api, team_uid, self.phone2, 'admin')['jid']
        # создаем задачу
        task_jid = self.api.add_task(team_uid).json()['result']['jid']
        api2 = auth.login_another_user(self.url, self.phone2, self.code2)
        resp = api2.get_task(team_uid, task_jid).json()
        assert resp['error'] == const.ACCESS_DENIED


    @pytest.mark.negative
    def test_get_task_outsider(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # создаем задачу
        task_jid = self.api.add_task(team_uid).json()['result']['jid']
        api4 = auth.login_another_user(self.url, self.phone4, self.code4)
        resp = api4.get_task(team_uid, task_jid).json()
        assert resp['error'] == const.ACCESS_DENIED


    @pytest.mark.positive
    def test_edit_task_owner(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # создаем задачу
        task_jid = self.api.add_task(team_uid).json()['result']['jid']
        status = 'done'
        title = 'new_title'
        data = {
            'task_status': status,
            'title': title
        }
        resp = self.api.edit_task(team_uid, task_jid, data).json()
        assert 'error' not in resp
        assert resp['result']['jid'] == task_jid
        assert resp['result']['task_status'] == status
        assert resp['result']['title'] == title


    @pytest.mark.negative
    def test_edit_task_role_member_observer(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # добавляем участника
        observer_jid = func.add_contact(self.api, team_uid, self.phone2, 'member')['jid']
        # создаем задачу
        task_jid = self.api.add_task(team_uid).json()['result']['jid']
        self.api.add_observer(team_uid, task_jid, observer_jid)
        api2 = auth.login_another_user(self.url, self.phone2, self.code2)
        status = 'done'
        title = 'new_title'
        data = {
            'task_status': status,
            'title': title
        }
        resp = api2.edit_task(team_uid, task_jid, data).json()
        assert resp['error'] == const.INVALID_DATA
        error_text = 'Изменение этого поля невозможно'
        assert resp['details']['title'] == error_text
        assert resp['details']['task_status'] == error_text


    @pytest.mark.negative
    def test_edit_task_outsider(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # создаем задачу
        task_jid = self.api.add_task(team_uid).json()['result']['jid']
        status = 'done'
        title = 'new_title'
        data = {
            'task_status': status,
            'title': title
        }
        api4 = auth.login_another_user(self.url, self.phone4, self.code4)
        resp = api4.edit_task(team_uid, task_jid, data).json()
        assert resp['error'] == const.ACCESS_DENIED


    @pytest.mark.positive
    def test_delete_task_owner(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # создаем задачу
        task_jid = self.api.add_task(team_uid).json()['result']['jid']
        resp = self.api.delete_task(team_uid, task_jid).json()
        assert 'error' not in resp
        assert resp['result']['jid'] == task_jid
        assert resp['result']['is_archive']


    @pytest.mark.negative
    def test_delete_task_role_member_observer(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # добавляем участника
        observer_jid = func.add_contact(self.api, team_uid, self.phone2, 'member')['jid']
        # создаем задачу
        task_jid = self.api.add_task(team_uid).json()['result']['jid']
        self.api.add_observer(team_uid, task_jid, observer_jid)
        api2 = auth.login_another_user(self.url, self.phone2, self.code2)
        resp = api2.delete_task(team_uid, task_jid).json()
        assert resp['error'] == const.ACCESS_DENIED


    @pytest.mark.negative
    def test_delete_task_outsider(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # создаем задачу
        task_jid = self.api.add_task(team_uid).json()['result']['jid']
        api4 = auth.login_another_user(self.url, self.phone4, self.code4)
        resp = api4.delete_task(team_uid, task_jid).json()
        assert resp['error'] == const.ACCESS_DENIED


    @pytest.mark.positive
    def test_add_checklist_owner(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # создаем задачу
        task_jid = self.api.add_task(team_uid).json()['result']['jid']
        checklist_title = 'checklist_' + tools.generate_random_string()
        data = {'checklist_title': checklist_title}
        resp = self.api.edit_task(team_uid, task_jid, data).json()
        assert 'error' not in resp
        assert resp['result']['jid'] == task_jid
        assert resp['result']['checklist_title'] == checklist_title


    @pytest.mark.negative
    def test_add_checklist_outsider(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # создаем задачу
        task_jid = self.api.add_task(team_uid).json()['result']['jid']
        checklist_title = 'checklist_' + tools.generate_random_string()
        data = {'checklist_title': checklist_title}
        api4 = auth.login_another_user(self.url, self.phone4, self.code4)
        resp = api4.edit_task(team_uid, task_jid, data).json()
        assert resp['error'] == const.ACCESS_DENIED


    @pytest.mark.positive
    def test_edit_checklist_owner(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # создаем задачу
        checklist_title = 'checklist_' + tools.generate_random_string()
        data = {'checklist_title': checklist_title}
        task_jid = self.api.add_task(team_uid, data).json()['result']['jid']
        checklist_title = 'new_' + tools.generate_random_string()
        data = {'checklist_title': checklist_title}
        resp = self.api.edit_task(team_uid, task_jid, data).json()
        assert 'error' not in resp
        assert resp['result']['jid'] == task_jid
        assert resp['result']['checklist_title'] == checklist_title


    @pytest.mark.negative
    def test_edit_checklist_outsider(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # создаем задачу
        checklist_title = 'checklist_' + tools.generate_random_string()
        data = {'checklist_title': checklist_title}
        task_jid = self.api.add_task(team_uid, data).json()['result']['jid']
        checklist_title = 'new_' + tools.generate_random_string()
        data = {'checklist_title': checklist_title}
        api4 = auth.login_another_user(self.url, self.phone4, self.code4)
        resp = api4.edit_task(team_uid, task_jid, data).json()
        assert resp['error'] == const.ACCESS_DENIED


    @pytest.mark.positive
    def test_add_one_point_checklist_owner(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # создаем задачу
        task_jid = self.api.add_task(team_uid).json()['result']['jid']
        text = 'point_' + tools.generate_random_string()
        data = {'text': text}
        resp = self.api.add_points_checklist(team_uid, task_jid, data).json()
        assert 'error' not in resp
        assert resp['result']['text'] == text


    @pytest.mark.positive
    def test_add_points_checklist_owner(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # создаем задачу
        task_jid = self.api.add_task(team_uid).json()['result']['jid']
        data = [
            {'text': 'point1_' + tools.generate_random_string()},
            {'text': 'point2_' + tools.generate_random_string()},
            {'text': 'point3_' + tools.generate_random_string()},
        ]
        data_json = json.dumps(data)
        resp = self.api.add_points_checklist(team_uid, task_jid, data_json).json()
        assert 'error' not in resp
        for point in data:
            assert tools.is_items_exist_in_list_of_dict(
                resp['result'],
                'text',
                point['text']
            )


    @pytest.mark.negative
    def test_add_point_checklist_member(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # добавляем участников
        func.add_contact(self.api, team_uid, self.phone2, 'member')
        # создаем задачу
        task_jid = self.api.add_task(team_uid).json()['result']['jid']
        text = 'point_' + tools.generate_random_string()
        data = {'text': text}
        api2 = auth.login_another_user(self.url, self.phone2, self.code2)
        resp = api2.add_points_checklist(team_uid, task_jid, data).json()
        assert resp['error'] == const.ACCESS_DENIED


    @pytest.mark.negative
    def test_add_point_checklist_outsider(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # создаем задачу
        task_jid = self.api.add_task(team_uid).json()['result']['jid']
        text = 'point_' + tools.generate_random_string()
        data = {'text': text}
        api4 = auth.login_another_user(self.url, self.phone4, self.code4)
        resp = api4.add_points_checklist(team_uid, task_jid, data).json()
        assert resp['error'] == const.ACCESS_DENIED


    @pytest.mark.positive
    def test_get_checklist_owner(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # создаем задачу
        task_jid = self.api.add_task(team_uid).json()['result']['jid']
        text = 'point_' + tools.generate_random_string()
        data = {'text': text}
        self.api.add_points_checklist(team_uid, task_jid, data).json()
        resp = self.api.get_checklist(team_uid, task_jid).json()
        assert 'error' not in resp
        assert resp['result'][0]['text'] == text


    @pytest.mark.negative
    def test_get_checklist_member(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # добавляем участников
        func.add_contact(self.api, team_uid, self.phone2, 'member')
        # создаем задачу
        task_jid = self.api.add_task(team_uid).json()['result']['jid']
        text = 'point_' + tools.generate_random_string()
        data = {'text': text}
        self.api.add_points_checklist(team_uid, task_jid, data).json()
        api2 = auth.login_another_user(self.url, self.phone2, self.code2)
        resp = api2.get_checklist(team_uid, task_jid).json()
        assert resp['error'] == const.ACCESS_DENIED


    @pytest.mark.negative
    def test_get_checklist_outsider(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # создаем задачу
        task_jid = self.api.add_task(team_uid).json()['result']['jid']
        text = 'point_' + tools.generate_random_string()
        data = {'text': text}
        self.api.add_points_checklist(team_uid, task_jid, data).json()
        api4 = auth.login_another_user(self.url, self.phone4, self.code4)
        resp = api4.get_checklist(team_uid, task_jid).json()
        assert resp['error'] == const.ACCESS_DENIED


    @pytest.mark.positive
    def test_get_checklist_point_owner(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # создаем задачу
        task_jid = self.api.add_task(team_uid).json()['result']['jid']
        text = 'point_' + tools.generate_random_string()
        data = {'text': text}
        point_uid = self.api.add_points_checklist(team_uid, task_jid, data).json()['result']['uid']
        resp = self.api.get_checklist_point(team_uid, task_jid, point_uid).json()
        assert 'error' not in resp
        assert resp['result']['uid'] == point_uid
        assert resp['result']['text'] == text


    @pytest.mark.negative
    def test_get_checklist_point_member(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # добавляем участников
        func.add_contact(self.api, team_uid, self.phone2, 'member')
        # создаем задачу
        task_jid = self.api.add_task(team_uid).json()['result']['jid']
        text = 'point_' + tools.generate_random_string()
        data = {'text': text}
        point_uid = self.api.add_points_checklist(team_uid, task_jid, data).json()['result']['uid']
        api2 = auth.login_another_user(self.url, self.phone2, self.code2)
        resp = api2.get_checklist_point(team_uid, task_jid, point_uid).json()
        assert resp['error'] == const.ACCESS_DENIED


    @pytest.mark.positive
    def test_edit_checklist_point_owner(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # создаем задачу
        task_jid = self.api.add_task(team_uid).json()['result']['jid']
        text = 'point_' + tools.generate_random_string()
        data = {'text': text}
        point_uid = self.api.add_points_checklist(team_uid, task_jid, data).json()['result']['uid']
        data = {
            'done': True,
            'text': 'new_text',
            'sort_ordering': 99
        }
        resp = self.api.edit_checklist_point(team_uid, task_jid, point_uid, data).json()
        assert 'error' not in resp
        assert resp['result']['uid'] == point_uid
        assert resp['result']['done'] == data['done']
        assert resp['result']['text'] == data['text']
        assert resp['result']['sort_ordering'] == data['sort_ordering']


    @pytest.mark.positive
    def test_edit_checklist_point_member(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # добавляем участников
        func.add_contact(self.api, team_uid, self.phone2, 'member')
        # создаем задачу
        task_jid = self.api.add_task(team_uid).json()['result']['jid']
        text = 'point_' + tools.generate_random_string()
        data = {'text': text}
        point_uid = self.api.add_points_checklist(team_uid, task_jid, data).json()['result']['uid']
        data = {
            'done': True,
            'text': 'new_text',
            'sort_ordering': 99
        }
        api2 = auth.login_another_user(self.url, self.phone2, self.code2)
        resp = api2.edit_checklist_point(team_uid, task_jid, point_uid, data).json()
        assert resp['error'] == const.ACCESS_DENIED


    @pytest.mark.positive
    def test_delete_checklist_point_owner(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # создаем задачу
        task_jid = self.api.add_task(team_uid).json()['result']['jid']
        text = 'point_' + tools.generate_random_string()
        data = {'text': text}
        point_uid = self.api.add_points_checklist(team_uid, task_jid, data).json()['result']['uid']
        resp = self.api.delete_checklist_point(team_uid, task_jid, point_uid).json()
        resp2 = self.api.get_checklist(team_uid, task_jid).json()
        assert 'error' not in resp
        assert resp['result'] is None
        assert not resp2['result']


    @pytest.mark.negative
    def test_delete_checklist_point_invalid_uid(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # создаем задачу
        task_jid = self.api.add_task(team_uid).json()['result']['jid']
        resp = self.api.delete_checklist_point(team_uid, task_jid, self.invalid_point_uid).json()
        assert resp['error'] == const.NOT_FOUND


    @pytest.mark.negative
    def test_delete_checklist_point_member(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # добавляем участников
        func.add_contact(self.api, team_uid, self.phone2, 'member')
        # создаем задачу
        task_jid = self.api.add_task(team_uid).json()['result']['jid']
        text = 'point_' + tools.generate_random_string()
        data = {'text': text}
        point_uid = self.api.add_points_checklist(team_uid, task_jid, data).json()['result']['uid']
        api2 = auth.login_another_user(self.url, self.phone2, self.code2)
        resp = api2.delete_checklist_point(team_uid, task_jid, point_uid).json()
        assert resp['error'] == const.ACCESS_DENIED


    @pytest.mark.positive
    def test_delete_checklist_owner(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # создаем задачу
        task_jid = self.api.add_task(team_uid).json()['result']['jid']
        text = 'point_' + tools.generate_random_string()
        data = {'text': text}
        self.api.add_points_checklist(team_uid, task_jid, data).json()
        resp = self.api.delete_checklist(team_uid, task_jid).json()
        resp2 = self.api.get_checklist(team_uid, task_jid).json()
        assert 'error' not in resp
        assert not resp['result']
        assert not resp2['result']


    @pytest.mark.positive
    def test_delete_checklist_outsider(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # создаем задачу
        task_jid = self.api.add_task(team_uid).json()['result']['jid']
        text = 'point_' + tools.generate_random_string()
        data = {'text': text}
        self.api.add_points_checklist(team_uid, task_jid, data).json()
        api4 = auth.login_another_user(self.url, self.phone4, self.code4)
        resp = api4.delete_checklist(team_uid, task_jid).json()
        assert resp['error'] == const.ACCESS_DENIED


    @pytest.mark.positive
    def test_get_tags_owner(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        data = {
            'tags': ['привет', 'hello', '555']
        }
        data_json = json.dumps(data)
        self.api.add_task(team_uid, data_json).json()['result']
        resp = self.api.get_tags(team_uid).json()
        assert 'error' not in resp
        for tag in data['tags']:
            assert tools.is_items_exist_in_list_of_dict(
                resp['result'],
                'name',
                tag
            )


    @pytest.mark.positive
    def test_get_tags_member(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # добавляем участников
        func.add_contact(self.api, team_uid, self.phone2, 'member')
        data = {
            'tags': ['привет', 'hello', '555']
        }
        data_json = json.dumps(data)
        self.api.add_task(team_uid, data_json).json()['result']
        api2 = auth.login_another_user(self.url, self.phone2, self.code2)
        resp = api2.get_tags(team_uid).json()
        assert 'error' not in resp
        for tag in data['tags']:
            assert tools.is_items_exist_in_list_of_dict(
                resp['result'],
                'name',
                tag
            )


    @pytest.mark.negative
    def test_get_tags_outsider(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        data = {
            'tags': ['привет', 'hello', '555']
        }
        data_json = json.dumps(data)
        self.api.add_task(team_uid, data_json).json()['result']
        api4 = auth.login_another_user(self.url, self.phone4, self.code4)
        resp = api4.get_tags(team_uid).json()
        assert resp['error'] == const.ACCESS_DENIED


    @pytest.mark.positive
    def test_add_reminds_to_me(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # добавляем задачу
        task = self.api.add_task(team_uid).json()['result']
        task_jid = task['jid']
        task_owner = task['owner']
        remind_date = tools.get_datetime_iso_string(datetime.datetime.now() + datetime.timedelta(days=5))
        data = {
            'chat': task_jid,
            'fire_at': remind_date,
        }
        data = json.dumps(data)
        resp = self.api.add_reminds(team_uid, data).json()
        assert 'error' not in resp['result']
        assert tools.is_items_exist_in_list_of_dict(
            [resp['result']],
            'fire_at',
            remind_date
        )
        assert tools.is_items_exist_in_list_of_dict(
            [resp['result']],
            'target',
            task_owner
        )


    @pytest.mark.positive
    def test_add_reminds_to_two_users(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # добавляем участника
        observer_jid = func.add_contact(self.api, team_uid, self.phone2)['jid']
        # добавляем задачу
        data = {"observers": [observer_jid]}
        data = json.dumps(data)
        task = self.api.add_task(team_uid, data).json()['result']
        task_jid = task['jid']
        task_owner = task['owner']
        remind_date = tools.get_datetime_iso_string(datetime.datetime.now() + datetime.timedelta(days=5))
        data = {
            'chat': task_jid,
            'fire_at': remind_date,
            'target': [task_owner, observer_jid]

        }
        data = json.dumps(data)
        resp = self.api.add_reminds(team_uid, data).json()
        assert 'error' not in resp['result']
        assert tools.is_items_exist_in_list_of_dict(
            resp['result'],
            'fire_at',
            remind_date
        )
        for jid in [task_owner, observer_jid]:
            assert tools.is_items_exist_in_list_of_dict(
                resp['result'],
                'target',
                jid
            )


    @pytest.mark.positive
    def test_add_reminds_observer(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # добавляем участника
        observer_jid = func.add_contact(self.api, team_uid, self.phone2)['jid']
        # добавляем задачу
        data = {"observers": [observer_jid]}
        data = json.dumps(data)
        task = self.api.add_task(team_uid, data).json()['result']
        task_jid = task['jid']
        task_owner = task['owner']
        remind_date = tools.get_datetime_iso_string(datetime.datetime.now() + datetime.timedelta(days=5))
        data = {
            'chat': task_jid,
            'fire_at': remind_date,
            'target': [task_owner, observer_jid]

        }
        data = json.dumps(data)
        api2 = auth.login_another_user(self.url, self.phone2, self.code2)
        resp = api2.add_reminds(team_uid, data).json()
        assert 'error' not in resp['result']
        assert tools.is_items_exist_in_list_of_dict(
            resp['result'],
            'fire_at',
            remind_date
        )
        for jid in [task_owner, observer_jid]:
            assert tools.is_items_exist_in_list_of_dict(
                resp['result'],
                'target',
                jid
            )


    @pytest.mark.negative
    def test_add_reminds_member(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # добавляем участника
        observer_jid = func.add_contact(self.api, team_uid, self.phone2)['jid']
        # добавляем задачу
        task = self.api.add_task(team_uid).json()['result']
        task_jid = task['jid']
        task_owner = task['owner']
        remind_date = tools.get_datetime_iso_string(datetime.datetime.now() + datetime.timedelta(days=5))
        data = {
            'chat': task_jid,
            'fire_at': remind_date,
            'target': [task_owner, observer_jid]
        }
        data = json.dumps(data)
        api2 = auth.login_another_user(self.url, self.phone2, self.code2)
        resp = api2.add_reminds(team_uid, data).json()
        assert resp['error'] == const.INVALID_DATA
        assert resp['details']['chat'] == 'Неизвестный чат'


    @pytest.mark.positive
    def test_get_reminds_owner(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # добавляем участника
        observer_jid = func.add_contact(self.api, team_uid, self.phone2)['jid']
        # добавляем задачу
        data = {"observers": [observer_jid]}
        data = json.dumps(data)
        task = self.api.add_task(team_uid, data).json()['result']
        task_jid = task['jid']
        task_owner = task['owner']
        remind_date = tools.get_datetime_iso_string(datetime.datetime.now() + datetime.timedelta(days=5))
        data = {
            'chat': task_jid,
            'fire_at': remind_date,
            'target': [task_owner, observer_jid]
        }
        data = json.dumps(data)
        resp = self.api.add_reminds(team_uid, data).json()
        resp1 = self.api.get_reminds(team_uid).json()
        assert 'error' not in resp1
        assert resp['result'][0] == resp1['result'][0]


    @pytest.mark.positive
    def test_get_reminds_observer(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # добавляем участника
        observer_jid = func.add_contact(self.api, team_uid, self.phone2)['jid']
        # добавляем задачу
        data = {"observers": [observer_jid]}
        data = json.dumps(data)
        task = self.api.add_task(team_uid, data).json()['result']
        task_jid = task['jid']
        task_owner = task['owner']
        remind_date = tools.get_datetime_iso_string(datetime.datetime.now() + datetime.timedelta(days=5))
        data = {
            'chat': task_jid,
            'fire_at': remind_date,
            'target': [task_owner, observer_jid]
        }
        data = json.dumps(data)
        resp = self.api.add_reminds(team_uid, data).json()
        api2 = auth.login_another_user(self.url, self.phone2, self.code2)
        resp1 = api2.get_reminds(team_uid).json()
        assert 'error' not in resp1
        assert resp['result'][1] == resp1['result'][0]


    @pytest.mark.positive
    def test_get_reminds_member(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # добавляем участника
        observer_jid = func.add_contact(self.api, team_uid, self.phone2)['jid']
        # добавляем задачу
        task = self.api.add_task(team_uid).json()['result']
        task_jid = task['jid']
        task_owner = task['owner']
        remind_date = tools.get_datetime_iso_string(datetime.datetime.now() + datetime.timedelta(days=5))
        data = {
            'chat': task_jid,
            'fire_at': remind_date,
            'target': [task_owner]
        }
        data = json.dumps(data)
        self.api.add_reminds(team_uid, data).json()
        api2 = auth.login_another_user(self.url, self.phone2, self.code2)
        resp1 = api2.get_reminds(team_uid).json()
        assert 'error' not in resp1
        assert not resp1['result']


    @pytest.mark.positive
    def test_get_remind_owner(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # добавляем задач
        task = self.api.add_task(team_uid).json()['result']
        task_jid = task['jid']
        remind_date = tools.get_datetime_iso_string(datetime.datetime.now() + datetime.timedelta(days=5))
        data = {
            'chat': task_jid,
            'fire_at': remind_date,
        }
        remind = self.api.add_reminds(team_uid, data).json()
        remind_uid = remind['result']['uid']
        resp = self.api.get_remind(team_uid, remind_uid).json()
        assert 'error' not in resp
        assert remind['result'] == resp['result']


    @pytest.mark.positive
    def test_delete_remind_owner(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # добавляем задач
        task = self.api.add_task(team_uid).json()['result']
        task_jid = task['jid']
        remind_date = tools.get_datetime_iso_string(datetime.datetime.now() + datetime.timedelta(days=5))
        data = {
            'chat': task_jid,
            'fire_at': remind_date,
        }
        remind = self.api.add_reminds(team_uid, data).json()
        remind_uid = remind['result']['uid']
        resp = self.api.delete_remind(team_uid, remind_uid).json()
        resp1 = self.api.get_remind(team_uid, remind_uid).json()
        assert resp['result'] is None
        assert resp1['error'] == const.NOT_FOUND


    @pytest.mark.positive
    def test_delete_remind_member(self):
        # создаем команду
        team_uid = func.add_team(self.api)['uid']
        # добавляем участника
        observer_jid = func.add_contact(self.api, team_uid, self.phone2)['jid']
        # добавляем задач
        task = self.api.add_task(team_uid).json()['result']
        task_jid = task['jid']
        remind_date = tools.get_datetime_iso_string(datetime.datetime.now() + datetime.timedelta(days=5))
        data = {
            'chat': task_jid,
            'fire_at': remind_date,
        }
        remind = self.api.add_reminds(team_uid, data).json()
        remind_uid = remind['result']['uid']
        api2 = auth.login_another_user(self.url, self.phone2, self.code2)
        resp = api2.delete_remind(team_uid, remind_uid).json()
        assert resp['error'] == const.NOT_FOUND

