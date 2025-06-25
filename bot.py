import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters, CallbackQueryHandler
import os
from dotenv import load_dotenv
import aiohttp
import sys
from telegram.constants import ChatAction
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

if not TELEGRAM_TOKEN or not DEEPSEEK_API_KEY:
    print("Ошибка: Не заданы TELEGRAM_TOKEN или DEEPSEEK_API_KEY в .env")
    sys.exit(1)

DEFAULT_MODEL = "deepseek-chat"
REASONER_MODEL = "deepseek-reasoner"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я бот с DeepSeek. Напиши мне что-нибудь.")

async def model_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("Обычная модель", callback_data=DEFAULT_MODEL),
            InlineKeyboardButton("Думающая модель", callback_data=REASONER_MODEL)
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выберите модель:", reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    model = query.data
    context.user_data['model'] = model
    model_name = "Обычная" if model == DEFAULT_MODEL else "Думающая"
    await query.edit_message_text(text=f"Вы выбрали: {model_name} модель")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text

    # Показываем, что бот печатает
    await update.message.chat.send_action(action=ChatAction.TYPING)

    # Получаем выбранную модель (по умолчанию обычная)
    model = context.user_data.get('model', DEFAULT_MODEL)

    # Получаем историю диалога пользователя
    history = context.user_data.get('history', [])
    # Добавляем новое сообщение пользователя
    history.append({"role": "user", "content": user_message})

    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}"},
            json={
                "model": model,
                "messages": history
            }
        ) as response:
            if response.status == 200:
                data = await response.json()
                answer = data["choices"][0]["message"]["content"]
            else:
                answer = f"Ошибка при обращении к DeepSeek API: {await response.text()}"

    # Добавляем ответ ассистента в историю
    history.append({"role": "assistant", "content": answer})
    # Сохраняем обновлённую историю
    context.user_data['history'] = history

    await update.message.reply_text(answer)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("model", model_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()