from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
import gspread
import os
import json
from google.oauth2.service_account import Credentials
from datetime import datetime

# ================= CONFIG =================
BOT_TOKEN = os.environ.get("BOT_TOKEN")
SPREADSHEET_NAME = "BOT Keuangan"

# ================= GOOGLE SHEET =================
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

creds_dict = json.loads(os.environ.get("GOOGLE_CREDENTIAL_JSON"))
creds = Credentials.from_service_account_file(
    creds_dict,
    scopes=SCOPES
)
client = gspread.authorize(creds)
spreadsheet = client.open(SPREADSHEET_NAME)

# ================= HELPER =================
def rupiah(n):
    return f"Rp {int(n):,}".replace(",", ".")

def now_full():
    return datetime.now().strftime("%A, %d %B %Y | %H:%M WIB")

def today():
    return datetime.now().strftime("%Y-%m-%d")

# ================= USER SHEET =================
def get_user_sheet(chat_id):
    sheet_name = f"user_{chat_id}"
    try:
        ws = spreadsheet.worksheet(sheet_name)
    except gspread.exceptions.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(
            title=sheet_name,
            rows=1000,
            cols=10
        )
        ws.append_row([
            "timestamp",
            "type",
            "amount",
            "note",
            "leak",
            "saldo_sisa"
        ])
    return ws

def get_today_rows(ws):
    rows = ws.get_all_records()
    return [r for r in rows if r["timestamp"].startswith(today())]

def get_total(ws, tipe):
    return sum(int(r["amount"]) for r in get_today_rows(ws) if r["type"] == tipe)

def get_last_balance(ws):
    rows = ws.get_all_records()
    return int(rows[-1]["saldo_sisa"]) if rows else 0

def save_record(ws, tipe, amount, note):
    pemasukan = get_total(ws, "Pemasukan")
    pengeluaran = get_total(ws, "Pengeluaran")
    saldo = get_last_balance(ws)

    leak = "NO"

    if tipe == "Pemasukan":
        pemasukan += amount
        saldo += amount
    else:
        pengeluaran += amount
        saldo -= amount
        if pengeluaran > pemasukan:
            leak = "YES"

    ws.append_row([
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        tipe,
        amount,
        note,
        leak,
        saldo
    ])

    return pemasukan, pengeluaran, saldo, leak

# ================= SPREADSHEET SHARE =================
def create_and_share_user_sheet(chat_id, email):
    # Ambil sheet user
    ws = get_user_sheet(chat_id)
    # Share SPREADSHEET ke email
    spreadsheet.share(email, perm_type='user', role='writer', notify=True)
    return ws


def get_sheet_url(ws):
    return f"{spreadsheet.url}#gid={ws.id}"

# ================= COMMAND =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["💰 Pemasukan", "💸 Pengeluaran"],
        ["📊 Summary", "📋 Catatan Hari Ini"],
        ["📈 Lihat Spreadsheet"],
    ]
    await update.message.reply_text(
        "🤖 Bot Keuangan Aktif\nKelola keuangan harianmu dengan rapi 💸",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
    )

# ================= HANDLER =================
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    chat_id = update.effective_chat.id
    ws = get_user_sheet(chat_id)

    # ================= INPUT Pemasukan/Pengeluaran =================
    if text in ["💰 Pemasukan", "💸 Pengeluaran"]:
        context.user_data["type"] = "Pemasukan" if "Pemasukan" in text else "Pengeluaran"
        await update.message.reply_text("Masukkan nominal transaksi:")

    elif text.isdigit() and "type" in context.user_data:
        context.user_data["amount"] = int(text)
        await update.message.reply_text("Tambahkan catatan transaksi:")

    elif "amount" in context.user_data:
        loading = await update.message.reply_text("⏳ Sedang memproses...")

        tipe = context.user_data["type"]
        amount = context.user_data["amount"]
        note = text

        pemasukan, pengeluaran, saldo, leak = save_record(ws, tipe, amount, note)
        sisa = pemasukan - pengeluaran
        context.user_data.clear()

        msg = (
            f"✅ {tipe} berhasil dicatat\n\n"
            f"🗓️ {now_full()}\n\n"
            f"Nominal : {rupiah(amount)}\n"
            f"Catatan : {note}\n\n"
            f"📊 Ringkasan Hari Ini\n"
            f"• Pemasukan : {rupiah(pemasukan)}\n"
            f"• Pengeluaran : {rupiah(pengeluaran)}\n"
            f"• Sisa dana : {rupiah(sisa)}\n"
        )

        if pemasukan > 0 and sisa <= pemasukan * 0.2 and leak == "NO":
            msg += "\n⚠️ Sisa dana hari ini tinggal 20%."

        if leak == "YES":
            msg += "\n🚨 LEAK! Pengeluaran melebihi pemasukan."

        await loading.edit_text(msg)

    # ================= MENU =================
    elif text == "📊 Summary":
        loading = await update.message.reply_text("⏳ Sedang memproses...")

        pemasukan = get_total(ws, "Pemasukan")
        pengeluaran = get_total(ws, "Pengeluaran")
        saldo = get_last_balance(ws)

        await loading.edit_text(
            f"📊 SUMMARY HARI INI\n\n"
            f"🗓️ {now_full()}\n\n"
            f"💰 Pemasukan : {rupiah(pemasukan)}\n"
            f"💸 Pengeluaran : {rupiah(pengeluaran)}\n"
            f"🧮 Sisa dana : {rupiah(pemasukan - pengeluaran)}\n"
            f"💼 Saldo total : {rupiah(saldo)}"
        )

    elif text == "📋 Catatan Hari Ini":
        loading = await update.message.reply_text("⏳ Sedang memproses...")

        data = get_today_rows(ws)
        if not data:
            await loading.edit_text("📭 Belum ada catatan hari ini.")
            return

        msg = "📋 CATATAN HARI INI\n\n"
        for r in data:
            msg += (
                f"{r['timestamp']}\n"
                f"{r['type']} | {rupiah(r['amount'])}\n"
                f"Sisa : {rupiah(r['saldo_sisa'])}\n"
                f"Leak : {r['leak']}\n\n"
            )

        await loading.edit_text(msg)

    # ================= LIHAT SPREADSHEET =================
    elif text == "📈 Lihat Spreadsheet":
        await update.message.reply_text(
            "✉️ Masukkan email kamu untuk share spreadsheet (contoh: kamu@mail.com):"
        )
        context.user_data["await_email"] = True

    # ================= HANDLE EMAIL =================
    elif "await_email" in context.user_data:
        email = text.strip()
        context.user_data.pop("await_email")

        loading = await update.message.reply_text("⏳ Sedang membuat dan share spreadsheet...")

        # Share spreadsheet user ke email
        ws = create_and_share_user_sheet(chat_id, email)

        await loading.edit_text(f"✅ Spreadsheet Keuangan Kamu sudah siap!\n📊 {get_sheet_url(ws)}")

# ================= MAIN =================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    print("🤖 Bot keuangan running...")
    app.run_polling()

if __name__ == "__main__":
    main()
