import os
import json
from telegram import Update, Bot
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))
CHANNEL = os.getenv("CHANNEL")
DB_FILE = "database.json"

bot = Bot(token=BOT_TOKEN)

# Ensure DB file exists
def ensure_db():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, "w") as f:
            json.dump({}, f)

# Load data
def load_data():
    with open(DB_FILE, "r") as f:
        return json.load(f)

# Save data
def save_data(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

# Start command
def start(update: Update, context: CallbackContext):
    user = update.message.from_user
    chat_id = update.message.chat_id
    try:
        member = bot.get_chat_member(CHANNEL, user.id)
        if member.status not in ["member", "administrator", "creator"]:
            update.message.reply_text(f"🚫 पहले हमारे चैनल से join करें: {CHANNEL}")
            return
    except Exception:
        update.message.reply_text(f"🚫 पहले हमारे चैनल से join करें: {CHANNEL}")
        return

    update.message.reply_text(
        "🌹 Welcome to Number Saver Bot\n\n"
        "📌 Send a phone number (with +country) or @username to get details.\n\n"
        "👑 Owner can add entries using:\n"
        "/add +919876543210|Name|Father|Village|State|Country"
    )

# Add command (Owner only)
def add_entry(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if user_id != OWNER_ID:
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
    except Exception:
        update.message.reply_text(
            "❌ Format error.\nUse:\n/add +919876543210|Name|Father|Village|State|Country"
        )

# Lookup handler
def handle_message(update: Update, context: CallbackContext):
    text = update.message.text.strip()
    data = load_data()
    info = data.get(text)
    if info:
        msg = "\n".join([f"{k}: {v}" for k, v in info.items()])
        update.message.reply_text(f"📞 Details:\n{msg}")
    else:
        update.message.reply_text("❌ No record found.")

# Main function
def main():
    ensure_db()
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("add", add_entry))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()