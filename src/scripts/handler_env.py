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
        [InlineKeyboardButton("DELTA_THRESHOLD", callback_data="delta_threshold")],
        [InlineKeyboardButton("Отмена", callback_data="cancel_settings")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выберите параметр для изменения:", reply_markup=reply_markup)
    return SETTING_CHOICE


async def settings_cancel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text("Изменение настроек отменено.")
    else:
        await update.message.reply_text("Изменение настроек отменено.")
    return ConversationHandler.END


async def settings_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    # Если нажата кнопка отмены, завершаем диалог
    if query.data == "cancel_settings":
        return await settings_cancel_callback(update, context)

    context.user_data["setting_param"] = query.data

    # Отправляем сообщение с запросом ввода нового значения и добавляем inline кнопку для отмены
    keyboard = [
        [InlineKeyboardButton("Отмена", callback_data="cancel_settings")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        text=f"Введите новое значение для {query.data}:",
        reply_markup=reply_markup
    )
    return SETTING_VALUE


async def settings_value(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Если пришёл callback-запрос (например, нажатие кнопки "Отмена")
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        if query.data == "cancel_settings":
            await query.edit_message_text("Изменение настроек отменено.")
            return ConversationHandler.END

    # Если пришёл текстовое сообщение
    new_value = update.message.text.strip()
    if new_value.lower() in ["отмена", "/cancel"]:
        await update.message.reply_text("Изменение настроек отменено.")
        return ConversationHandler.END

    setting_param = context.user_data.get("setting_param")
    update_env_variable(setting_param.upper(), new_value)
    await update.message.reply_text(f"Параметр {setting_param} обновлён на {new_value}.")
    return ConversationHandler.END

