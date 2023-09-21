import logging, json, os, datetime, asyncio
from telegram import Update
from telegram.ext import filters, ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler
from project.openai_utils import get_new_resume, get_incremental_resume, estimate_tokens

MAX_TOKEN_SIZE = int(os.environ['MAX_TOKEN_SIZE'])
CHAT_CHECK_INTERVAL=60 # Check every hour if chat had updates
MINUTE_DURATION_SECONDS=60
MIN_MESSAGES_BEFORE_AUTO_RESUME=20

class Chatbot:
    def __init__(self,message_buf) -> None:
        self.message_buf = message_buf
        self.max_token_size = MAX_TOKEN_SIZE

    def reset_buf(self,chat_id, context):
        self.message_buf[chat_id]['messages'] = []
        self.message_buf[chat_id]['cur_size'] = 0
        self.message_buf[chat_id]['context'] = context
        self.message_buf[chat_id].pop('resume')

    def init_buf(self,chat_id,context):
        self.message_buf[chat_id] = {'messages' : [], 'cur_size' : 0, 'context' : context, 'selfResumeEnabled' : True }

    def do_resume(self,chat_id):
        if('resume' not in self.message_buf[chat_id] and self.message_buf[chat_id]['cur_size'] == 0):
            return "Non c'è niente di cui fare il riassunto, demente"
        if('resume' not in self.message_buf[chat_id] and self.message_buf[chat_id]['cur_size'] > 0):
            result = get_new_resume(self.message_buf[chat_id]['messages'])
        if('resume' in self.message_buf[chat_id] and self.message_buf[chat_id]['cur_size'] > 0):
            result = get_incremental_resume(self.message_buf[chat_id]['resume'],self.message_buf[chat_id]['messages'])
        if('resume' in self.message_buf[chat_id] and self.message_buf[chat_id]['cur_size'] == 0):
            result = self.message_buf[chat_id]['resume']
        self.message_buf[chat_id] = {'messages' : [], 'cur_size' : 0, 'resume' : result, 'selfResumeEnabled' : self.message_buf[chat_id]['selfResumeEnabled']}
        return result


    async def log(self,update: Update, context: ContextTypes.DEFAULT_TYPE):
        if(update.message is not None):
            chat_id = update.effective_chat.id
            text = update.message.text
            username = update.message.from_user.full_name
            date = update.message.date
            #await context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)
            if(chat_id not in self.message_buf):
                self.init_buf(chat_id,context)
            message_data = { 'username' : username, 'text' : text, 'date' : date }
            self.message_buf[chat_id]['messages'].append(message_data)
            cur_size = self.message_buf[chat_id]['cur_size'] + estimate_tokens(json.dumps(message_data['username'])) + estimate_tokens(json.dumps(message_data['text']))
            self.message_buf[chat_id]['cur_size'] = cur_size
            self.message_buf[chat_id]['context'] = context
            logging.info(f"id: {chat_id}, message: {text}, cur_size: {cur_size}")
            # Resume interno automatico
            if(cur_size > self.max_token_size):
                self.do_resume(chat_id)
        
    async def chat_check_loop(self):
        await asyncio.sleep(MINUTE_DURATION_SECONDS*CHAT_CHECK_INTERVAL)
        await self.chat_check()
        await self.chat_check_loop()

    async def chat_check(self):
        now = datetime.datetime.now(datetime.timezone.utc)
        for chat_id in self.message_buf:
            if self.message_buf[chat_id]['selfResumeEnabled']:
                context = self.message_buf[chat_id]['context']
                buf_len = len(self.message_buf[chat_id]['messages'])
                if(buf_len > MIN_MESSAGES_BEFORE_AUTO_RESUME):
                    last_message_date = self.message_buf[chat_id]['messages'][-1]['date']
                    elapsed_seconds = (now - last_message_date).total_seconds()
                    if(elapsed_seconds / 60 > CHAT_CHECK_INTERVAL):
                        await context.bot.send_message(chat_id, text="È passato un pò dall'ultimo messaggio! Sto per fare il riassunto")
                        await self.resumeMessages(chat_id)

    def get_chat_id(self,update: Update):
        return update.effective_chat.id
    
    async def toggleSelfResume_handler(self, update: Update, context : ContextTypes.DEFAULT_TYPE):
        chat_id = self.get_chat_id(update)
        if self.message_buf[chat_id]['selfResumeEnabled']:
            self.message_buf[chat_id]['selfResumeEnabled'] = False
            await context.bot.send_message(chat_id, text="Riassunti automatici disattivati!")
        else:
            self.message_buf[chat_id]['selfResumeEnabled'] = True
            await context.bot.send_message(chat_id, text="Riassunti automatici attivati!")

        
    async def resetMessages(self,chat_id,context):
        self.reset_buf(chat_id,context)
        await context.bot.send_message(chat_id, text="Storico messaggi resettato!")

    async def resetMessages_handler(self,update: Update, context : ContextTypes.DEFAULT_TYPE):
        chat_id = self.get_chat_id(update)
        await self.resetMessages(chat_id,context)

    async def resumeMessages(self,chat_id):
        context = self.message_buf[chat_id]['context']
        resume_msg = await context.bot.send_message(chat_id, text=f"Dimensione token: {self.message_buf[chat_id]['cur_size']}. Elaborazione riassunto, attendi...")
        logging.info(f"Richiesta riassunto messaggi su {chat_id}")
        result = self.do_resume(chat_id)
        logging.info(f"Riassunto elaborato: {result}")
        await resume_msg.edit_text(result)
        await self.resetMessages(chat_id,context)

    async def resumeMessages_handler(self,update: Update, context : ContextTypes.DEFAULT_TYPE):
        chat_id = self.get_chat_id(update)
        if(chat_id not in self.message_buf):
            await  context.bot.send_message(chat_id, text=f"C'è solo un messaggio, non farò il riassunto!")
        await self.resumeMessages(chat_id)

    async def help_handler(self,update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = self.get_chat_id(update)
        await context.bot.send_message(chat_id, text=f"Ciao, sono SuntoBot di Rami!\
\nServo a creare un riassunto abbastanza confuso dei messaggi nei gruppi, grazie a GPT.\
\n Istruzioni:\n Inseriscimi in una chat di gruppo. \n \
Usa il comando /resume per avere il riassunto\n \
Usa il comando /reset per resettare il log della conversazione.\n \
Il reset dello storico è automatico a ogni riassunto. \n \
Ogni {CHAT_CHECK_INTERVAL} minuti se ci sono almeno {MIN_MESSAGES_BEFORE_AUTO_RESUME} messaggi parte un riassunto automatico. \n \
Se preferisci disattivarlo, usa il comando /selfResume.\n \
PRIVACY NOTICE: Il bot gira su un muletto del creatore e al momento i messaggi sono conservati in RAM, non vengono salvati \
o usati per altri fini. Il progetto è open source e lo trovi su https://github.com/mraminella/suntobot .\n \
Buon rimbambimento!")
