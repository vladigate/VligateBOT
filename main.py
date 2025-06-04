import logging
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, ContextTypes
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# СТАДИИ
GOAL, TARIFF, NAME, PHONE, CITY, DESCRIPTION, CONTACT, CONFIRM, OFFER = range(9)

# Telegram Token
TOKEN = "7669134121:AAEJfFPOk-Br92s74tcGXW5Fb1izDC7qRPM"

# Google Sheets setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)
sheet = client.open_by_key("1JyMp0g6krlalSWZcduOwFE_A1C8Ut9WiQSMOJR9UXsw").sheet1

# Логирование
logging.basicConfig(level=logging.INFO)

# Тарифы
tariffs = {
    "Базовый (5 000 ₽)": "✅ Входит:\n• Фото объекта\n• Аналитика\n• Консультация\n• Объявление\n• Реклама\n• Чек-лист\n• Рекомендации",
    "Премиум (10 000 ₽)": "✅ Входит всё из базового +\n• Шаблоны документов\n• Помощь с показами\n• Поддержка\n• Инструкции по переговорам"
}

# Шаг 1 — Старт
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = [["Продать недвижимость"], ["Купить недвижимость"], ["Подобрать новостройку"]]
    await update.message.reply_text(
        "Привет! 👋 Добро пожаловать в Vligate — ваш проводник в мире недвижимости.\n\n"
        "💬 О нас:\n• Работаем от 5 000 ₽\n• Прозрачный онлайн-сервис\n• Помощь с продажей, покупкой, новостройками\n• Без скрытых комиссий\n\n"
        "Что вы хотите сделать?",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return GOAL

# Шаг 2 — Цель
async def goal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["goal"] = update.message.text
    if update.message.text == "Подобрать новостройку":
        context.user_data["tariff"] = "Новостройки (0 ₽)"
        return await name(update, context)
    else:
        keyboard = [["Базовый (5 000 ₽)"], ["Премиум (10 000 ₽)"]]
        await update.message.reply_text("Выберите тариф:", reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True))
        return TARIFF

# Шаг 3 — Тариф
async def tariff(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["tariff"] = update.message.text
    await update.message.reply_text(f"{tariffs[update.message.text]}")
    await update.message.reply_text("Как вас зовут?", reply_markup=ReplyKeyboardRemove())
    return NAME

# Шаг 4 — Имя
async def name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["name"] = update.message.text
    await update.message.reply_text("Укажите номер телефона:")
    return PHONE

# Шаг 5 — Телефон
async def phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["phone"] = update.message.text
    await update.message.reply_text("В каком городе или районе находится объект?")
    return CITY

# Шаг 6 — Город
async def city(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["city"] = update.message.text
    await update.message.reply_text("Опишите, что именно вы хотите (тип, срочность, особенности):")
    return DESCRIPTION

# Шаг 7 — Описание
async def description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["description"] = update.message.text
    keyboard = [["Telegram"], ["WhatsApp"], ["Телефонный звонок"]]
    await update.message.reply_text("Как удобнее с вами связаться?", reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True))
    return CONTACT

# Шаг 8 — Контакт
async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["contact"] = update.message.text
    keyboard = [["✅ Принимаю и соглашаюсь"], ["❌ Не согласен"]]
    await update.message.reply_text(
        "📄 Ознакомьтесь с документами:\n• https://vligate.tilda.ws/oferta\n• https://vligate.tilda.ws/privacy\n\n"
        "Подтвердите согласие:",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return OFFER

# Шаг 9 — Подтверждение оферты
async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    accepted = update.message.text
    if accepted.startswith("❌"):
        await update.message.reply_text("К сожалению, без согласия мы не можем продолжить. Спасибо за интерес к Vligate!")
        return ConversationHandler.END

    context.user_data["offer"] = "Согласен"

    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    row = [
        now,
        context.user_data["name"],
        context.user_data["phone"],
        context.user_data["city"],
        context.user_data["goal"],
        context.user_data["tariff"],
        context.user_data["description"],
        context.user_data["contact"],
        context.user_data["offer"]
    ]
    sheet.append_row(row)

    await update.message.reply_text("🎉 Спасибо! Заявка принята. Свяжемся в течение 30–60 минут.")
    return ConversationHandler.END

# Сценарий
def main():
    app = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            GOAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, goal)],
            TARIFF: [MessageHandler(filters.TEXT & ~filters.COMMAND, tariff)],
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, name)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, phone)],
            CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, city)],
            DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, description)],
            CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, contact)],
            OFFER: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm)],
        },
        fallbacks=[]
    )

    app.add_handler(conv_handler)
    app.run_polling()

if __name__ == "__main__":
    main()




