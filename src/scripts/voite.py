import json
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)
from ratings import main

# Новые состояния для диалога голосования
VOTE_CHOICE, VOTE_VALUE, VOTE_COUNT = range(3)


async def vote_count_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    vote_count_str = update.message.text
    try:
        vote_count = int(vote_count_str)
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите корректное число для количества голосов.")
        return VOTE_COUNT  # Остаёмся в этом состоянии до получения корректного ввода

    company_id = context.user_data.get("selected_company")
    vote_value = context.user_data.get("vote_value")

    # Используем введённое число для вызова функционала голосования
    await vote_for_company(company_id, vote_value, vote_count)

    await update.message.reply_text(
        f"Отдано {vote_count} голосов с весом {vote_value} за компанию с id {company_id}."
    )
    return ConversationHandler.END


async def vote_for_company(company_id: str, vote_value: str, vote_count: int) -> None:
    main(company_id, vote_value, vote_count)
    print(f"Отдано {vote_count} голосов с весом {vote_value} за компанию {company_id}.")


async def vote_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Загрузка данных из data.json
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
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выберите компанию для голосования:", reply_markup=reply_markup)
    return VOTE_CHOICE


async def vote_company_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data["selected_company"] = query.data
    # Клавиатура для выбора голоса: 5 или 1
    keyboard = [
        [InlineKeyboardButton("5", callback_data="5"), InlineKeyboardButton("1", callback_data="1")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text="Выберите голос (5 или 1):", reply_markup=reply_markup)
    return VOTE_VALUE


async def vote_value_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    vote_value = query.data
    context.user_data["vote_value"] = vote_value
    await query.edit_message_text(text=f"Введите количество голосов для выбранного голоса {vote_value}:")
    return VOTE_COUNT


async def vote_count_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    vote_count_str = update.message.text
    try:
        vote_count = int(vote_count_str)
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите корректное число для количества голосов.")
        return VOTE_COUNT  # Остаёмся в этом состоянии до получения корректного ввода

    company_id = context.user_data.get("selected_company")
    vote_value = context.user_data.get("vote_value")

    # Вызываем функцию голосования, которая содержит print
    await vote_for_company(company_id, vote_value, vote_count)

    await update.message.reply_text(
        f"Отдано {vote_count} голосов с весом {vote_value} за компанию с id {company_id}."
    )
    return ConversationHandler.END


async def vote_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Голосование отменено.")
    return ConversationHandler.END
