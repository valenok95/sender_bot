import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram import F
from datetime import datetime

# Получаем переменные окружения
API_TOKEN = os.environ.get('API_TOKEN')
ADMINS = os.environ.get('ADMINS')
TARGET_CHATS = os.environ.get('TARGET_CHATS').split(',')

# Проверка наличия необходимых переменных окружения
if not API_TOKEN or not TARGET_CHATS:
    raise ValueError("Необходимо установить переменные окружения: API_TOKEN, TARGET_CHATS")

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Хранение идентификаторов сообщений для редактирования
message_ids = {}


def contains(list, string):
    return string in list


async def is_admin(username: str) -> bool:
    """Проверка, является ли пользователь администратором чата по никнейму."""
    try:
        # Проверяем, есть ли пользователь с указанным никнеймом среди администраторов
        if contains(ADMINS, username.lower()):
            return True
        else:
            return False
    except Exception as e:
        logger.error(f"Ошибка при получении информации о администраторах чата: {e}")
        return False


@dp.message(Command('start'))
async def send_welcome(message: types.Message):
    await message.reply("Привет!\nЯ бот-закреп!\nОтправь мне любое сообщение, а я тебе обязательно его закреплю.")
    logger.info(
        f"{datetime.now()} - Пользователь {message.from_user.username} (ID: {message.from_user.id}) запустил бота.")


@dp.message(F.text)
async def echo(message: types.Message):
    admin_status = await is_admin(message.from_user.username)

    logger.info(
        f"{datetime.now()} - Пользователь {message.from_user.username} (ID: {message.from_user.id}) отправил сообщение: '{message.text}'")

    if admin_status:
        try:
            # Отправляем сообщение в целевые чаты
            for chat in TARGET_CHATS:
                # logger('пытаемся отправить новое сообщения в цикле, текущий чат ' + str(chat))
                msg = await bot.send_message(chat, message.text)
                # Закрепляем сообщения
                await bot.pin_chat_message(chat_id=chat, message_id=msg.message_id)
                # Сохраняем идентификаторы сообщений для редактирования
                message_ids[chat] = msg.message_id

        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения: {e}")
    else:
        await message.reply("У вас нет прав для отправки сообщений.")


@dp.edited_message(F.text)
async def handle_edited_message(message: types.Message):

        logger.info(
            f"{datetime.now()} - Пользователь {message.from_user.username} (ID: {message.from_user.id})  изменил текст сообщения на: '{message.text}'")

        for chat in TARGET_CHATS:
            # Редактируем сообщения в целевых чатах
            await bot.edit_message_text(message.text, chat_id=chat, message_id=message_ids[chat])


async def main():
    try:
        logger.info('проверка api token: ' + str(API_TOKEN))
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Произошла ошибка при запуске бота: {e}")
        await asyncio.sleep(5)  # Пауза перед повторной попыткой


if __name__ == '__main__':
    asyncio.run(main())
