import logging, os
from telegram.ext import filters, ApplicationBuilder, CommandHandler, MessageHandler
from project.chatbot import Chatbot

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


if __name__ == '__main__':
    # manager = multiprocessing.Manager()
    #message_buf = manager.dict()
    message_buf = {}
    chatbot = Chatbot(message_buf)
    application = ApplicationBuilder().token(os.environ['TELEGRAM_BOT_KEY']).build()
    
    message_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), chatbot.log)
    start_handler = CommandHandler('start', chatbot.start)
    getAllMessages_handler = CommandHandler('getAllMessages', chatbot.getAllMessages)
    resetMessages_handler = CommandHandler('reset', chatbot.resetMessages)
    resumeMessages_handler = CommandHandler('resume', chatbot.resumeMessages)
    
    application.add_handler(start_handler)
    application.add_handler(message_handler)
    application.add_handler(getAllMessages_handler)
    application.add_handler(resetMessages_handler)
    application.add_handler(resumeMessages_handler)

    application.run_polling()
