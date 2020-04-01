### Описание
Данный репозиторий содержит автотесты для проекта messenger.

### Требования к ПО
- Установленный Python 3.x - [www.python.org/getit/](https://www.python.org/getit/)
- Установленный инструмент для работы с виртуальными окружениями virtualenv
```bash
pip install virtualenv
```

### Копирование репозитория и установка зависимостей
##### Установка на Linux и MacOS
```bash
git clone https://github.com/arkuz/messenger_api_tests
cd messenger_tests
virtualenv env
env/scripts/activate
pip install -r requirements.txt
```

##### Установка на Windows
```bash
git clone https://github.com/arkuz/messenger_api_tests
cd messenger_tests
virtualenv env
cd env/scripts
activate.bat
pip install -r requirements.txt
```

### Запуск тестов
Перед запуском тестов необходимо перейти в каталог проекта `messenger_api_tests`.

Аргументы запуска:
- -s - показывать принты в процессе выпонения
- -v - verbose режим, чтобы видеть, какие тесты были запущены
- --html=report.html --self-contained-html - генерация автономного отчета
##### Запуск всех тестов
```bash
py.test -s -v --html=report.html --self-contained-html
```

##### Запуск всех тестов в пакете
```bash
py.test -s -v tests/api
```

##### Запуск помеченных тестов (positive, negative и т.п.)
```bash
py.test -s -v -m positive tests/api
```

##### Запуск тестового модуля
```bash
py.test -s -v tests/api/test_auth.py
```

##### Запуск тестового класса
```bash
py.test -s -v tests/api/test_auth.py::TestAuth
```

##### Запуск конкретного теста
```bash
py.test -s -v tests/api/test_auth.py::TestAuth::test_sms_login_valid_phone
```