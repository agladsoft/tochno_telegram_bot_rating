from telegram.ext import Application, CommandHandler
from handlers import start_handler, stop_handler
from src.settings import setting


def main() -> None:
    app = Application.builder().token(setting.TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("stop", stop_handler))

    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
