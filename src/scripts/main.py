import asyncio
from telegram.ext import Application, CommandHandler
from src.scripts.handlers import start_handler, stop_handler
from src.settings import get_settings
from src.scripts.handler_env import *
from src.scripts.handler_vote import *
from src.scripts.logger import app_logger as logger


async def no_access(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("У вас нет прав для выполнения этой команды.")


def main() -> None:
    app = Application.builder().token(get_settings().TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("stop", stop_handler))

    settings_handler = ConversationHandler(
        entry_points=[CommandHandler("settings", settings_start, filters=filters.User(user_id=get_settings().USER_ID))],
        states={
            SETTING_CHOICE: [
                CallbackQueryHandler(settings_choice, pattern="^(proxy|rating|delta_threshold|cancel_settings)$")],
            SETTING_VALUE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, settings_value),
                CallbackQueryHandler(settings_cancel_callback, pattern="^cancel_settings$")
            ],
        },
        fallbacks=[CommandHandler("cancel", settings_cancel_callback)],
    )
    app.add_handler(settings_handler)

    # Обработчик для голосования
    vote_handler = ConversationHandler(
        entry_points=[CommandHandler("vote", vote_start, filters=filters.User(user_id=get_settings().USER_ID))],
        states={
            VOTE_CHOICE: [
                CallbackQueryHandler(vote_company_choice, pattern=r"^\d+$"),
                CallbackQueryHandler(vote_cancel, pattern="^cancel_vote$")
            ],
            VOTE_VALUE: [
                CallbackQueryHandler(vote_value_choice, pattern="^(5|1)$"),
                CallbackQueryHandler(vote_cancel, pattern="^cancel_vote$")
            ],
            VOTE_COUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, vote_count_choice),
                CallbackQueryHandler(vote_cancel, pattern="^cancel_vote$")
            ],
        },
        fallbacks=[CommandHandler("cancel", vote_cancel)],
    )
    app.add_handler(vote_handler)

    app.add_handler(MessageHandler(filters.COMMAND & ~filters.User(user_id=get_settings().USER_ID), no_access))

    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":

    while True:
        logger.info("Запуск бота...")
        main()
        logger.info("Бот остановлен.")
