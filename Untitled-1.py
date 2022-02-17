import telegram
TELEGRAM_CHAT_ID= 1018602579

def send_message(bot, message):
    """Отправка сообщений ботом в телеграм."""
    try:
        
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except telegram.error:
        raise telegram.error(f'Ошибка при отправке сообщения:')

TELEGRAM_TOKEN = '5271259412:AAGsHdYhgMZmohGYLnSJxPhsymcLQikol-s'
bot = telegram.Bot(token=TELEGRAM_TOKEN)
message = 'тест'
send_message(bot, message)