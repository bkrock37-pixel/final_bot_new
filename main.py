import os
import json
import requests
from telegram import Update, Bot
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from dotenv import load_dotenv

# ✅ Load environment variables (.env or Replit secrets)
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN") or "YOUR_BOT_TOKEN"
OWNER_ID = int(os.getenv("OWNER_ID") or 123456789)
CHANNEL = os.getenv("CHANNEL_USERNAME") or "@YourChannelUsername"
DB_FILE = "database.json"

bot = Bot(token=BOT_TOKEN)

# ✅ Ensure database exists
def ensure_db():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, "w") as f:
            json.dump({}, f)

def load_data():
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

# ✅ Channel Join Check
def is_joined(user_id):
    try:
        member = bot.get_chat_member(CHANNEL, user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception:
        return False

# ✅ Auto Info Fetch (Legal Public API)
def get_auto_info(phone_number):
    try:
        num = phone_number.replace("+", "").strip()
        url = f"https://apilayer.net/api/validate?access_key=YOUR_NUMVERIFY_API_KEY&number={num}"
        res = requests.get(url).json()
        info = f"🌍 Country: {res.get('country_name', 'N/A')}\n"
        info += f"📞 Carrier: {res.get('carrier', 'N/A')}\n"
        info += f"📶 Line Type: {res.get('line_type', 'N/A')}\n"
        return info
    except:
        return "❌ No record found."

# ✅ /start Command
def start(update: Update, context: CallbackContext):
    user = update.message.from_user
    if not is_joined(user.id):
        update.message.reply_text(f"🚫 पहले हमारे चैनल को join करें: {CHANNEL}")
        return
    update.message.reply_text(
        "🌹 Welcome to Number Saver Bot!\n\n"
        "📌 Send a phone number (with +country) to get details.\n"
        "👑 Owner commands: /add /delete /backup"
    )

# ✅ /add Command
def add_entry(update: Update, context: CallbackContext):
    if update.message.from_user.id != OWNER_ID:
        update.message.reply_text("❌ Only owner can add entries.")
        return
    try:
        text = update.message.text.split(" ", 1)[1]
        phone, name, father, village, state, country = text.split("|")
        data = load_data()
        data[phone.strip()] = {
            "Name": name.strip(),
            "Father": father.strip(),
            "Village": village.strip(),
            "State": state.strip(),
            "Country": country.strip()
        }
        save_data(data)
        update.message.reply_text("✅ Entry added successfully!")
    except:
        update.message.reply_text("❌ Format error.\nUse:\n/add +919876543210|Name|Father|Village|State|Country")

# ✅ /delete Command
def delete_entry(update: Update, context: CallbackContext):
    if update.message.from_user.id != OWNER_ID:
        update.message.reply_text("❌ Only owner can delete entries.")
        return
    try:
        number = update.message.text.split(" ", 1)[1].strip()
        data = load_data()
        if number in data:
            del data[number]
            save_data(data)
            update.message.reply_text("🗑️ Entry deleted successfully!")
        else:
            update.message.reply_text("❌ Number not found in database.")
    except:
        update.message.reply_text("❌ Use:\n/delete +919876543210")

# ✅ /backup Command
def backup(update: Update, context: CallbackContext):
    if update.message.from_user.id != OWNER_ID:
        update.message.reply_text("❌ Only owner can use this command.")
        return
    ensure_db()
    with open(DB_FILE, "rb") as f:
        update.message.reply_document(f, filename="database_backup.json")

# ✅ Handle Numbers
def handle_message(update: Update, context: CallbackContext):
    user = update.message.from_user
    text = update.message.text.strip()

    if not is_joined(user.id):
        update.message.reply_text(f"🚫 पहले हमारे चैनल को join करें: {CHANNEL}")
        return

    data = load_data()
    if text in data:
        info = data[text]
        msg = "\n".join([f"{k}: {v}" for k, v in info.items()])
        update.message.reply_text(f"📋 Saved Info:\n{msg}")
    else:
        update.message.reply_text("📡 Searching public info...")
        update.message.reply_text(get_auto_info(text))

# ✅ Start Bot
def main():
    ensure_db()
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("add", add_entry))
    dp.add_handler(CommandHandler("delete", delete_entry))
    dp.add_handler(CommandHandler("backup", backup))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
