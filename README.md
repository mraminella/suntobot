
# Telegram Chat Resume Bot

This repository contains a Telegram bot written in Python that can do chat resume using GPT (Generative Pre-trained Transformer). It collects all messages within the chat where it is added, and can do resume of the chat via the `/resume` command. The chat history that is resumed can be reset using the `/reset` command.

## Requirements

This project requires four variables to be set up in a `.env` file:

```
TELEGRAM_BOT_KEY=<The Telegram bot key>
OPENAI_KEY=<The OpenAI API key>
MAX_TOKEN_SIZE=3000 # Max token size of historical chat before the app does internal auto-resume
COMPLETION_SIZE=600 # The completion size of the resume, the larger it gets, the more verbose a resume could be
```

## Project Structure

The project consists of the main `app.py` and two simple modules in `project/`:

* `chatbot.py`
* `openai_utils.py`

The project also contains a `Dockerfile` and `docker-compose.yml` to launch the application in a container.

## Usage

To run the bot, simply run `python3 app.py` or `docker-compose up` in the project directory.
