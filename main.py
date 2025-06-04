
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes,
    MessageHandler, filters, ConversationHandler
)

import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Настройка логов
logging.basicConfig(level=logging.INFO)

# Этапы разговора
GOAL, TARIFF, NAME, PHONE, CITY, DESCRIPTION, CONTACT, CONFIRM = range(8)

# Подключение к Google Таблице
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
gc = gspread.authorize(credentials)
spreadsheet = gc.open_by_url("https://docs.google.com/spreadsheets/d/1JyMp0g6krlalSWZcduOwFE_A1C8Ut9WiQSMOJR9UXsw/edit")
worksheet = spreadsheet.sheet1

# Сохранение данных
def save_to_sheet(data):
    worksheet.append_row([
        data.get("name", ""),
        data.get("phone", ""),
        data.get("city", ""),
        data.get("goal", ""),
        data.get("tariff", ""),
        data.get("description", ""),
        data.get("contact", "")
    ])

# Приветствие
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Привет! 👋\n"
        "Добро пожаловать в Vligate — ваш проводник в мире недвижимости.\n"
        "Мы — альтернатива риелторам: прозрачный и надёжный онлайн-сервис.\n\n"
        "💬 О нас:\n"
        "• Работаем по фиксированной цене — от 5 000 ₽\n"
        "• Помогаем с продажей, покупкой или подбором новостроек\n"
        "• Работаем в Твери и онлайн по всей России\n"
        "• Без % и скрытых комиссий\n\n"
        "Что вы хотите сделать?",
        reply_markup=ReplyKeyboardMarkup(
            [["Продать недвижимость", "Купить недвижимость", "Подобрать новостройку"]],
            one_time_keyboard=True,
            resize_keyboard=True
        )
    )
    return GOAL

async def goal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["goal"] = update.message.text
    if context.user_data["goal"] in ["Продать недвижимость", "Купить недвижимость"]:
        await update.message.reply_text(
            "Выберите тариф:",
            reply_markup=ReplyKeyboardMarkup(
                [["Базовый (5 000 ₽)", "Премиум (10 000 ₽)"]],
                one_time_keyboard=True,
                resize_keyboard=True
            )
        )
        return TARIFF
    else:
        context.user_data["tariff"] = "Новостройка (бесплатно)"
        await update.message.reply_text("Как вас зовут?")
        return NAME

async def tariff(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["tariff"] = update.message.text
    await update.message.reply_text("Как вас зовут?")
    return NAME

async def name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["name"] = update.message.text
    await update.message.reply_text("Укажите номер телефона для связи:")
    return PHONE

async def phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["phone"] = update.message.text
    await update.message.reply_text("В каком городе или районе находится объект?")
    return CITY

async def city(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["city"] = update.message.text
    await update.message.reply_text("Что именно вы хотите? (Кратко опишите)")
    return DESCRIPTION

async def description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["description"] = update.message.text
    await update.message.reply_text(
        "Как удобнее с вами связаться?",
        reply_markup=ReplyKeyboardMarkup(
            [["Telegram", "WhatsApp", "Телефонный звонок"]],
            one_time_keyboard=True,
            resize_keyboard=True
        )
    )
    return CONTACT

async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["contact"] = update.message.text
    await update.message.reply_text(
        "Примите ли вы условия оферты и согласие на обработку персональных данных?\n"
        "📄 Ознакомьтесь по ссылкам:\n"
        "• https://vligate.tilda.ws/oferta\n"
        "• https://vligate.tilda.ws/privacy\n",
        reply_markup=ReplyKeyboardMarkup(
            [["✅ Принимаю и соглашаюсь", "❌ Не согласен"]],
            one_time_keyboard=True,
            resize_keyboard=True
        )
    )
    return CONFIRM

async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text == "✅ Принимаю и соглашаюсь":
        save_to_sheet(context.user_data)
        await update.message.reply_text(
            "🎉 Спасибо! Мы уже получили вашу заявку.\n"
            "В течение 30–60 минут с вами свяжется менеджер Vligate (Влад).\n"
            "А пока загляните на наш сайт — vligate.tilda.ws"
        )
    else:
        await update.message.reply_text("Спасибо за интерес. Если передумаете — мы всегда на связи!")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Диалог завершён.")
    return ConversationHandler.END

app = ApplicationBuilder().token("ВАШ_ТОКЕН_БОТА").build()

conv = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        GOAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, goal)],
        TARIFF: [MessageHandler(filters.TEXT & ~filters.COMMAND, tariff)],
        NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, name)],
        PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, phone)],
        CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, city)],
        DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, description)],
        CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, contact)],
        CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm)],
    },
    fallbacks=[CommandHandler("cancel", cancel)]
)

app.add_handler(conv)
app.run_polling()
