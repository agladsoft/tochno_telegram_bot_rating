import asyncio
import json
import os

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ConversationHandler,
    ContextTypes,
)
from src.scripts.tasks.cel import send_vote_to_background
from src.scripts.parser import HtmlParser

# Новые состояния для диалога голосования
VOTE_CHOICE, VOTE_VALUE, VOTE_COUNT = range(3)


async def vote_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Загрузка данных из data.json
    if not os.path.isfile("data.json"):
        await HtmlParser.parse_top_developers()
    try:
        with open("data.json", "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        await update.message.reply_text(f"Ошибка загрузки данных: {e}")
        return ConversationHandler.END

    # Формируем клавиатуру с кнопками, где текст — название компании, а callback_data — post id
    keyboard = [
        [InlineKeyboardButton(info["name"], callback_data=post_id)]
        for post_id, info in data.items()
    ]
    # Добавляем кнопку отмены
    keyboard.append([InlineKeyboardButton("Отмена", callback_data="cancel_vote")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выберите компанию для голосования:", reply_markup=reply_markup)
    return VOTE_CHOICE


async def vote_company_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    # Если нажата кнопка отмены, завершаем диалог
    if query.data == "cancel_vote":
        return await vote_cancel(update, context)

    context.user_data["selected_company"] = query.data

    # Клавиатура для выбора голоса: 5 или 1 с кнопкой отмены
    keyboard = [
        [InlineKeyboardButton("5", callback_data="5"), InlineKeyboardButton("1", callback_data="1")],
        [InlineKeyboardButton("Отмена", callback_data="cancel_vote")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text="Выберите голос (5 или 1):", reply_markup=reply_markup)
    return VOTE_VALUE


async def vote_value_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    # Если нажата кнопка отмены, завершаем диалог
    if query.data == "cancel_vote":
        return await vote_cancel(update, context)

    vote_value = query.data
    context.user_data["vote_value"] = vote_value

    # Запрашиваем ввод количества голосов с возможностью отмены
    keyboard = [
        [InlineKeyboardButton("Отмена", callback_data="cancel_vote")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        text=f"Введите количество голосов для выбранного голоса {vote_value}:",
        reply_markup=reply_markup
    )
    return VOTE_COUNT


async def vote_count_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Если пользователь ввёл текст "Отмена" вручную
    text = update.message.text.strip()
    if text.lower() in ["отмена", "/cancel"]:
        await update.message.reply_text("Голосование отменено.")
        return ConversationHandler.END

    try:
        vote_count = int(text)
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите корректное число для количества голосов.")
        return VOTE_COUNT  # Остаёмся в этом состоянии до получения корректного ввода

    company_id = context.user_data.get("selected_company")
    vote_value = context.user_data.get("vote_value")


    await vote_for_company(company_id, vote_value, vote_count)

    await update.message.reply_text(
        "Запущено голосование отслеживайте в мониторинге"
    )
    return ConversationHandler.END


async def vote_for_company(company_id: str, vote_value: str, vote_count: int) -> None:
    send_vote_to_background(company_id, vote_value, vote_count)
    print(f"Отдано {vote_count} голосов с весом {vote_value} за компанию {company_id}.")


async def vote_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text("Голосование отменено.")
    else:
        await update.message.reply_text("Голосование отменено.")
    return ConversationHandler.END
