import logging, os, asyncio
from telegram.ext import filters, ApplicationBuilder, CommandHandler, MessageHandler
from project.chatbot import Chatbot


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.WARN
)

if __name__ == '__main__':
    message_buf = {}
    chatbot = Chatbot(message_buf)
    application = ApplicationBuilder().token(os.environ['TELEGRAM_BOT_KEY']).build()
    
    message_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), chatbot.log)
    help_handler = CommandHandler('help', chatbot.help_handler)
    resetMessages_handler = CommandHandler('reset', chatbot.resetMessages_handler)
    resumeMessages_handler = CommandHandler('resume', chatbot.resumeMessages_handler)
    toggleSelfResume_handler = CommandHandler('selfResume', chatbot.toggleSelfResume_handler)
    
    application.add_handler(help_handler)
    application.add_handler(message_handler)
    application.add_handler(resetMessages_handler)
    application.add_handler(resumeMessages_handler)
    application.add_handler(toggleSelfResume_handler)

    loop = asyncio.get_event_loop()

    loop.create_task(chatbot.chat_check_loop())
    loop.run_until_complete(asyncio.gather(application.run_polling()),chatbot.chat_check_loop())