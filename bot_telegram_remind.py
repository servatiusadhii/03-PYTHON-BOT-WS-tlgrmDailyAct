from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from datetime import datetime
import asyncio
import os

TOKEN = os.getenv("BOT_TOKEN")

# storage sederhana (per user)
user_notes = {}
user_reminders = {}

MENU = ReplyKeyboardMarkup(
    [
        ["1️⃣ Hari ini"],
        ["2️⃣ Catatan saya"],
        ["3️⃣ Reminder"],
        ["4️⃣ Exit"],
    ],
    resize_keyboard=True
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Halo!\n"
        "Gue asisten pribadi lo.\n\n"
        "Pilih menu di bawah 👇",
        reply_markup=MENU
    )

async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.message.from_user.id

    if text.startswith("1"):
        now = datetime.now()
        await update.message.reply_text(
            f"📅 Hari ini:\n"
            f"Hari: {now.strftime('%A')}\n"
            f"Tanggal: {now.strftime('%d %B %Y')}\n"
            f"Jam: {now.strftime('%H:%M:%S')}"
        )

    elif text.startswith("2"):
        context.user_data["mode"] = "note"
        await update.message.reply_text(
            "✍️ Kirim catatan lo.\n"
            "Gue simpan khusus buat lo."
        )

    elif text.startswith("3"):
        context.user_data["mode"] = "reminder"
        await update.message.reply_text(
            "⏰ Kirim reminder format:\n"
            "`HH:MM | pesannya`",
            parse_mode="Markdown"
        )

    elif text.startswith("4"):
        await update.message.reply_text(
            "👋 Sampai ketemu lagi!",
            reply_markup=None
        )

    else:
        await update.message.reply_text("❓ Pilih menu yang tersedia.")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    mode = context.user_data.get("mode")

    if mode == "note":
        user_notes.setdefault(user_id, []).append(update.message.text)
        await update.message.reply_text("✅ Catatan tersimpan.")
        context.user_data["mode"] = None

    elif mode == "reminder":
        try:
            time_part, msg = update.message.text.split("|", 1)
            hour, minute = map(int, time_part.strip().split(":"))
            now = datetime.now()
            target = now.replace(hour=hour, minute=minute, second=0)

            delay = (target - now).total_seconds()
            if delay < 0:
                await update.message.reply_text("⛔ Waktunya sudah lewat.")
                return

            async def send_reminder():
                await asyncio.sleep(delay)
                await update.message.reply_text(f"⏰ Reminder:\n{msg.strip()}")

            asyncio.create_task(send_reminder())
            await update.message.reply_text("⏳ Reminder diset.")
            context.user_data["mode"] = None

        except:
            await update.message.reply_text("❌ Format salah.")

    else:
        await update.message.reply_text("Pilih menu dulu ya 👇", reply_markup=MENU)

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu))
    app.add_handler(MessageHandler(filters.TEXT, handle_text))

    print("Bot berjalan...")
    app.run_polling()
