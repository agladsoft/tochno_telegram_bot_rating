import random
import asyncio
import contextlib
import re
from typing import Dict

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from src.scripts.parser import HtmlParser

# Глобальный словарь для хранения задач мониторинга по chat_id
monitor_tasks = {}


def get_keyboard() -> ReplyKeyboardMarkup:
    """
    Создает постоянную клавиатуру с командами.
    """
    keyboard = [
        ["/start", "/stop"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


async def get_difference_ratings(text: str):
    ratings = re.findall(r'\d+\.\d+', text)

    if len(ratings) < 2:
        return "Не удалось извлечь данные."
    difference = float(ratings[0]) - float(ratings[1])

    return f'Разница между 1 и 2 местом: {difference:.2f}'


async def monitor_site(chat_id: int, bot) -> None:
    """
    Непрерывно проверяет состояние сайта с периодичностью.
    Отправляет сообщение, если условие выполнено или с вероятностью 20% для информирования.
    Работает до тех пор, пока задача не будет отменена (команда /stop) или не сработает критическое условие.
    """
    with contextlib.suppress(asyncio.CancelledError):
        while True:
            html = await HtmlParser.parse_top_developers()
            if not html:
                await asyncio.sleep(30)
                continue
            await bot.send_message(chat_id, html)
            different = await get_difference_ratings(html)
            await bot.send_message(chat_id, different)
            await asyncio.sleep(30)


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик команды /start.
    Если мониторинг не запущен для данного чата, запускает асинхронный цикл,
    который периодически проверяет состояние сайта и отправляет сообщения.
    """
    chat_id = update.effective_chat.id
    if chat_id in monitor_tasks:
        await update.message.reply_text(
            """Мониторинг уже запущен! 🚀 \nОн будет работать до тех пор, пока разница между рейтингом первого и второго мест не станет больше или равной 0.1, или пока вы не нажмете команду /stop для завершения. Для остановки мониторинга просто введите /stop.""",
            reply_markup=get_keyboard()
        )
    else:
        task = asyncio.create_task(monitor_site(chat_id, context.bot))
        monitor_tasks[chat_id] = task
        await update.message.reply_text(
            """Мониторинг запущен! 🚀 \nОн будет работать до тех пор, пока разница между рейтингом первого и второго мест нестанет больше или равной 0.1, или пока вы не нажмете команду /stop для завершения. Для остановки мониторинга просто введите /stop.""",
            reply_markup=get_keyboard()
        )


async def stop_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик команды /stop.
    Останавливает запущенный мониторинг для данного чата.
    """
    chat_id = update.effective_chat.id
    if chat_id in monitor_tasks:
        monitor_tasks[chat_id].cancel()
        del monitor_tasks[chat_id]
        await update.message.reply_text(
            "Мониторинг остановлен.",
            reply_markup=get_keyboard()
        )
    else:
        await update.message.reply_text(
            "Мониторинг не был запущен.",
            reply_markup=get_keyboard()
        )
