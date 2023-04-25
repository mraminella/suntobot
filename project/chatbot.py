import logging, json, os
from telegram import Update
from telegram.ext import filters, ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler
from project.openai_utils import get_new_resume, get_incremental_resume, estimate_tokens

MAX_TOKEN_SIZE = int(os.environ['MAX_TOKEN_SIZE'])
class Chatbot:
    def __init__(self,message_buf) -> None:
        self.message_buf = message_buf
        self.max_token_size = MAX_TOKEN_SIZE

    def init_buf(self,chat_id):
        self.message_buf[chat_id] = {'messages' : [], 'cur_size' : 0}


    def do_resume(self,chat_id):
        if('resume' not in self.message_buf[chat_id] and self.message_buf[chat_id]['cur_size'] == 0):
            return "Non c'è niente di cui fare il riassunto, demente"
        if('resume' not in self.message_buf[chat_id] and self.message_buf[chat_id]['cur_size'] > 0):
            result = get_new_resume(self.message_buf[chat_id]['messages'])
        if('resume' in self.message_buf[chat_id] and self.message_buf[chat_id]['cur_size'] > 0):
            result = get_incremental_resume(self.message_buf[chat_id]['resume'],self.message_buf[chat_id]['messages'])
        if('resume' in self.message_buf[chat_id] and self.message_buf[chat_id]['cur_size'] == 0):
            result = self.message_buf[chat_id]['resume']
        self.message_buf[chat_id] = {'messages' : [], 'cur_size' : 0, 'resume' : result}
        return result


    async def log(self,update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        text = update.message.text
        username = update.message.from_user.full_name    
        #await context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)
        if(chat_id not in self.message_buf):
            self.init_buf(chat_id)
        message_data = { 'username' : username, 'text' : text }
        self.message_buf[chat_id]['messages'].append(message_data)
        cur_size = self.message_buf[chat_id]['cur_size'] +  estimate_tokens(json.dumps(message_data))
        self.message_buf[chat_id]['cur_size'] = cur_size
        logging.info(f"id: {chat_id}, message: {text}, cur_size: {cur_size}")        
        if(cur_size > self.max_token_size):
            self.do_resume(chat_id)
        
    async def getAllMessages(self,update: Update, context : ContextTypes.DEFAULT_TYPE):
        await context.bot.send_message(chat_id=update.effective_chat.id, text=self.message_buf[update.effective_chat.id]['messages'])

    async def resetMessages(self,update: Update, context : ContextTypes.DEFAULT_TYPE):
        self.init_buf(update.effective_chat.id)
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Storico messaggi resettato!")

    async def resumeMessages(self,update: Update, context : ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        if(chat_id not in self.message_buf):
            await  context.bot.send_message(chat_id=update.effective_chat.id, text=f"Sei serio?")
        resume_msg = await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Dimensione token: {self.message_buf[chat_id]['cur_size']}. Elaborazione riassunto, attendi...")
        logging.info(f"Richiesta riassunto messaggi su {chat_id}")
        result = self.do_resume(chat_id)
        logging.info(f"Riassunto elaborato: {result}")
        await resume_msg.edit_text(result)

    async def start(self,update: Update, context: ContextTypes.DEFAULT_TYPE):
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Ciao, sono SuntoBot di Rami!\nServo a creare un riassunto dei messaggi che ho ricevuto usando GPT.\n Istruzioni:\n Usa il comando /resume per avere il riassunto\n Usa il comando /reset per resettare il log della conversazione.\nIl reset dello storico è automatico a ogni riassunto.")
