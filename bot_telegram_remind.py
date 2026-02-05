from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from datetime import datetime
import random

TOKEN = "7948305758:AAFaWIHzR-N7mW0q6S_z7DlpIJpPVsFSV7w"

# Keyboard menu
menu = ReplyKeyboardMarkup(
    [
        ["1️⃣ Cek Hari Ini"],
        ["2️⃣ Info Hari Ini"],
        ["3️⃣ Exit"]
    ],
    resize_keyboard=True
)

# Command /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Halo 👋\nSilakan pilih menu:",
        reply_markup=menu
    )

async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    # MENU 1
    if "Cek Hari Ini" in text:
        now = datetime.now()
        hari = now.strftime("%A")
        tanggal = now.strftime("%d %B %Y")
        jam = now.strftime("%H:%M:%S")

        await update.message.reply_text(
            f"📅 Hari : {hari}\n"
            f"📆 Tanggal : {tanggal}\n"
            f"⏰ Jam : {jam}"
        )

    # MENU 2 (tanpa API)
    elif "Info Hari Ini" in text:
        cuaca = random.choice([
            "☀️ Cerah",
            "🌤️ Cerah Berawan",
            "☁️ Berawan",
            "🌧️ Hujan Ringan"
        ])
        suhu = random.randint(24, 33)

        await update.message.reply_text(
            "📊 Info Hari Ini\n"
            f"🌡️ Perkiraan Suhu : {suhu}°C\n"
            f"🌦️ Kondisi : {cuaca}\n\n"
            "⚠️ *Catatan:* ini hanya perkiraan sederhana.",
            parse_mode="Markdown"
        )

    # MENU 3
    elif "Exit" in text:
        await update.message.reply_text(
            "👋 Terima kasih!\nSampai jumpa.",
            reply_markup=None
        )

    else:
        await update.message.reply_text("❗ Silakan pilih menu yang tersedia")

if __name__ == "__main__":
    from telegram.request import HTTPXRequest

    request = HTTPXRequest(
        connect_timeout=20,
        read_timeout=20,
        write_timeout=20
    )

    app = (
        ApplicationBuilder()
        .token(TOKEN)
        .request(request)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT, handler))

    print("Bot berjalan...")
    app.run_polling(close_loop=False)

