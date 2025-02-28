import asyncio
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup
from telegram.ext import (
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)
from update_env import *

# Состояния для диалога изменения настроек
SETTING_CHOICE, SETTING_VALUE = range(2)


async def settings_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = [
        [InlineKeyboardButton("PROXY", callback_data="proxy")],
        [InlineKeyboardButton("Rating", callback_data="rating")],
        [InlineKeyboardButton("DELTA_THRESHOLD", callback_data="delta_threshold")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выберите параметр для изменения:", reply_markup=reply_markup)
    return SETTING_CHOICE


async def settings_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data["setting_param"] = query.data
    await query.edit_message_text(text=f"Введите новое значение для {query.data}:")
    return SETTING_VALUE


async def settings_value(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    new_value = update.message.text
    setting_param = context.user_data.get("setting_param")

    update_env_variable(setting_param.upper(), new_value)
    await update.message.reply_text(f"Параметр {setting_param} обновлён на {new_value}.")
    return ConversationHandler.END


async def settings_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Изменение настроек отменено.")
    return ConversationHandler.END
