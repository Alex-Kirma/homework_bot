import telegram
import telegram.ext
import telegram.error

import requests
import os
import logging
import sys
import time

from http import HTTPStatus

from dotenv import load_dotenv

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

VERDICTS_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(stream=sys.stdout)
formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)
logger.addHandler(handler)


def send_message(bot, message):
    """Отправка сообщений ботом в телеграм."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except telegram.error:
        logger.error('Не удалоcь отправить сообщение')
    else:
        logger.info('Сообщение успешно отправленно!')
    return True


def get_api_answer(current_timestamp):
    """Получение запроса с эндпоинта и проверка его на доступность."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        homework_statuses = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params=params
        )
        status_code = homework_statuses.status_code
        if status_code != HTTPStatus.OK:
            logger.error(f'Недоступен эндпоинт, код ответа {status_code}')
            raise requests.exceptions.HTTPError('Ошибка доступа к эндпоинту')
        return homework_statuses.json()
    except Exception as error:
        logger.error(f'Сбой при доступе к энд поинту, ошибка: {error}')
        raise Exception(f'Возникло исключение, ошибка: {error}')


def check_response(response):
    """Проверка статуса запроса homeworks."""
    try:
        homeworks = response['homeworks']
        type_homeworks = isinstance(homeworks, list)
        if not type_homeworks:
            logger.error(f'В ответе API пришел не список {type_homeworks}')
            raise TypeError('Ожидаемый ответ API не список')
    except KeyError as error:
        logger.error(f'Нет ожидаемых ключей в ответе API {error}')
        raise KeyError('Нет ключа в ответе API')
    return homeworks


def parse_status(homework):
    """Парсинг списка домашних заданий."""
    try:
        homework_name = homework['homework_name']
        homework_status = homework['status']
    except KeyError as error:
        logger.error('Ошибка ключа')
        raise KeyError(f'Ключ не найден, ошибка: {error}')
    if homework_status in VERDICTS_STATUSES:
        logger.debug('Статус работы обновлен')
    else:
        if homework_status not in VERDICTS_STATUSES:
            logger.error('Такого статуса не существует')
            raise KeyError('Ключ не найден')
    verdict = VERDICTS_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверка переменных окружения env на доступность."""
    env = {
        PRACTICUM_TOKEN: 'PRACTICUM_TOKEN',
        TELEGRAM_TOKEN: 'TELEGRAM_TOKEN',
        TELEGRAM_CHAT_ID: 'TELEGRAM_CHAT_ID',
    }
    for key, value in env.items():
        if key == '' or key is None:
            logger.critical(
                f'Отсутствует обязательная переменная: {value}'
            )
            return False
    return True


def main():
    """Основная логика работы бота."""
    if check_tokens() is False:
        sys.exit()

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    error_message = ''
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            for homework in homeworks:
                verdict = parse_status(homework)
                send_message(bot, verdict)
                current_timestamp = response['current_date']
            time.sleep(RETRY_TIME)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            if message != error_message:
                test_message = send_message(bot, message)
            if test_message:
                error_message = message


if __name__ == '__main__':
    main()
