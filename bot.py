import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import requests

TELEGRAM_TOKEN = "7689009154:AAFCIQuA1CnVeB4aQRKLT2Pkd7v-lkzGmVM"
DEEPSEEK_API_KEY = "sk-4fcb4d7931a14614862ff532f3053109"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я бот с DeepSeek. Напиши мне что-нибудь.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text

    response = requests.post(
        "https://api.deepseek.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}"},
        json={
            "model": "deepseek-chat",
            "messages": [
                {"role": "user", "content": user_message}
            ]
        }
    )
    if response.ok:
        data = response.json()
        answer = data["choices"][0]["message"]["content"]
    else:
        answer = f"Ошибка при обращении к DeepSeek API: {response.text}"

    await update.message.reply_text(answer)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()