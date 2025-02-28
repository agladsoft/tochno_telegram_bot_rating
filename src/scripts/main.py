from telegram.ext import Application, CommandHandler
from handlers import start_handler, stop_handler
from src.settings import setting
from handler_env import *
from voite import *


def main() -> None:
    app = Application.builder().token(setting.TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("stop", stop_handler))

    settings_handler = ConversationHandler(
        entry_points=[CommandHandler("settings", settings_start)],
        states={
            SETTING_CHOICE: [CallbackQueryHandler(settings_choice, pattern="^(proxy|rating|delta_threshold)$")],
            SETTING_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, settings_value)],
        },
        fallbacks=[CommandHandler("cancel", settings_cancel)],
    )
    app.add_handler(settings_handler)

    # Обработчик для голосования
    vote_handler = ConversationHandler(
        entry_points=[CommandHandler("vote", vote_start)],
        states={
            VOTE_CHOICE: [CallbackQueryHandler(vote_company_choice, pattern=r"^\d+$")],
            VOTE_VALUE: [CallbackQueryHandler(vote_value_choice, pattern="^(5|1)$")],
            VOTE_COUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, vote_count_choice)],
        },
        fallbacks=[CommandHandler("cancel", vote_cancel)],
    )
    app.add_handler(vote_handler)

    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
