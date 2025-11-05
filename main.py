import os
import json
import requests
from telegram import Update, Bot
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))
CHANNEL = os.getenv("CHANNEL_USERNAME")
DB_FILE = "database.json"

bot = Bot(token=BOT_TOKEN)


# ✅ Ensure database file exists
def ensure_db():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, "w") as f:
            json.dump({}, f)


# ✅ Load/Save data
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


# ✅ Auto Info (Country, Sim, Line Type)
def get_number_info(phone_number):
    api_key = os.getenv("NUMVERIFY_API_KEY")
    if not api_key:
        return "⚠️ API Key missing. Add NUMVERIFY_API_KEY in secrets."

    num = phone_number.replace("+", "").strip()
    url = f"http://apilayer.net/api/validate?access_key={api_key}&number={num}&format=1"

    try:
        response = requests.get(url)
        data = response.json()
        if data.get("valid"):
            country = data.get("country_name", "Unknown")
            carrier = data.get("carrier", "Unknown")
            line_type = data.get("line_type", "Unknown")

            return (
                f"🌍 Country: {country}\n"
                f"📱 Carrier: {carrier}\n"
                f"📶 Line Type: {line_type}"
            )
        else:
            return "❌ Invalid or unregistered number."
    except Exception as e:
        print("Error fetching info:", e)
        return "⚠️ Could not fetch number info."


# ✅ /start Command
def start(update: Update, context: CallbackContext):
    user = update.message.from_user
    if not is_joined(user.id):
        update.message.reply_text(f"🚫 पहले हमारे चैनल को join करें: {CHANNEL}")
        return

    update.message.reply_text(
        "🌹 Welcome to Number Saver Bot\n\n"
        "📌 Send a phone number (with +country) to get details.\n"
        "👑 Owner commands: /add /delete /backup"
    )


# ✅ /add Command (Owner Only)
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
        update.message.reply_text(
            "❌ Format error.\nUse:\n/add +919876543210|Name|Father|Village|State|Country"
        )


# ✅ /delete Command (Owner Only)
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
            update.message.reply_text("❌ Number not found.")
    except:
        update.message.reply_text("❌ Use:\n/delete +919876543210")


# ✅ /backup Command (Owner Only)
def backup(update: Update, context: CallbackContext):
    if update.message.from_user.id != OWNER_ID:
        update.message.reply_text("❌ Only owner can use this command.")
        return
    ensure_db()
    with open(DB_FILE, "rb") as f:
        update.message.reply_document(f, filename="database_backup.json")


# ✅ Handle Number Messages
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
    elif text.startswith("+") or text.isdigit():
        update.message.reply_text("📡 Searching public info...")
        info = get_number_info(text)
        update.message.reply_text(info)
    else:
        update.message.reply_text("❌ Invalid input. Please send a valid number with +country code.")


# ✅ Main Function
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
