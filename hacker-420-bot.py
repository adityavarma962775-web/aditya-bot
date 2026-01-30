import telebot
import requests
import time
import random
import string
import threading

# --- CONFIGURATION ---
API_TOKEN = '8550288258:AAEU9XjS3_8XPPyqlIGo3KrvzmPMdCGAeik' 
ADMIN_ID = 6131454126  # Is ID ke alawa koi admin command nahi chala payega          

bot = telebot.TeleBot(API_TOKEN)
users = set() 
user_emails = {} 
active_checks = {}

# --- SECURITY CHECK ---
def check_admin(message):
    if message.from_user.id == ADMIN_ID:
        return True
    bot.reply_to(message, "🚫 **ACCESS DENIED**\nSirf Admin hi ye command use kar sakta hai.")
    return False

# --- MAIL.TM API FUNCTIONS ---
def get_mail_tm_domain():
    try:
        res = requests.get("https://api.mail.tm/domains").json()
        return res['hydra:member'][0]['domain']
    except:
        return "mail.tm"

def create_mail_tm_account(custom_user=None):
    domain = get_mail_tm_domain()
    username = custom_user.lower() if custom_user else ''.join(random.choice(string.ascii_lowercase + string.digits) for i in range(10))
    email = f"{username}@{domain}"
    password = "Password123!"
    
    payload = {"address": email, "password": password}
    try:
        res = requests.post("https://api.mail.tm/accounts", json=payload)
        if res.status_code == 201:
            login_res = requests.post("https://api.mail.tm/token", json=payload).json()
            return email, login_res['token']
        return None, None
    except:
        return None, None

def auto_check_logic(chat_id, email, token):
    headers = {"Authorization": f"Bearer {token}"}
    start_time = time.time()
    seen_ids = set()

    while active_checks.get(chat_id) == email and (time.time() - start_time) < 600:
        try:
            res = requests.get("https://api.mail.tm/messages", headers=headers).json()
            messages = res.get('hydra:member', [])
            for msg in messages:
                if msg['id'] not in seen_ids:
                    full_msg = requests.get(f"https://api.mail.tm/messages/{msg['id']}", headers=headers).json()
                    output = (
                        "⚡ **NEW OTP RECEIVED** ⚡\n"
                        "━━━━━━━━━━━━━━━━━━\n"
                        f"👤 **From:** {full_msg['from']['address']}\n"
                        f"📝 **Subject:** {full_msg['subject']}\n\n"
                        f"🔢 **OTP / Message:**\n`{full_msg['intro']}`\n"
                        "━━━━━━━━━━━━━━━━━━"
                    )
                    bot.send_message(chat_id, output, parse_mode='Markdown')
                    seen_ids.add(msg['id'])
        except: pass
        time.sleep(2)

# --- PUBLIC COMMANDS ---

@bot.message_handler(commands=['start'])
def start(message):
    users.add(message.chat.id)
    # Aditya Branding Highlighted
    welcome_text = (
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "🌟 **WELCOME TO ADITYA INFORMATION BOT** 🌟\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "Main aapka fast Temp-Mail aur OTP bot hoon.\n\n"
        "📖 Sabhi commands ke liye `/help` likhein."
    )
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

@bot.message_handler(commands=['help'])
def help_command(message):
    help_text = (
        "📖 **AVAILABLE COMMANDS**\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "📧 /email - Random temp mail\n"
        "✍️ /custom `<name>` - Apna naam ka email\n"
        "🔢 /otp - Test OTP generate karein\n"
        "🗑 /delete - Current session band karein\n"
    )
    # Admin section only for you
    if message.from_user.id == ADMIN_ID:
        help_text += (
            "\n🛠 **ADMIN ONLY**\n"
            "⚙️ /admin - Bot stats dekhein\n"
            "📢 /broadcast - Sabko message bhejein\n"
            "📋 /logs - System health dekhein"
        )
    bot.send_message(message.chat.id, help_text, parse_mode='Markdown')

@bot.message_handler(commands=['email', 'custom'])
def handle_mail_request(message):
    chat_id = message.chat.id
    cmd = message.text.split()
    custom_name = cmd[1] if len(cmd) > 1 and cmd[0] == '/custom' else None
    
    bot.send_message(chat_id, "⏳ Generating your secure email...")
    email, token = create_mail_tm_account(custom_name)
    
    if email:
        user_emails[chat_id] = email
        active_checks[chat_id] = email
        bot.send_message(chat_id, f"📧 **Email:** `{email}`\n🔥 Auto-refresh: **ON** (10 Mins)", parse_mode='Markdown')
        threading.Thread(target=auto_check_logic, args=(chat_id, email, token), daemon=True).start()
    else:
        bot.reply_to(message, "❌ Error! Username taken or server down.")

@bot.message_handler(commands=['otp'])
def manual_otp(message):
    otp = ''.join(random.choice("0123456789") for i in range(6))
    bot.reply_to(message, f"🔢 **Test OTP:** `{otp}`", parse_mode='Markdown')

@bot.message_handler(commands=['delete'])
def delete_session(message):
    active_checks[message.chat.id] = None
    bot.reply_to(message, "🗑 Session closed. Emails cleared.")

# --- SECURE ADMIN COMMANDS ---

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if not check_admin(message): return
    active_count = len([x for x in active_checks.values() if x])
    stats = (
        "🛠 **ADITYA'S CONTROL PANEL**\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"👤 Total Users: {len(users)}\n"
        f"⚡ Live Sessions: {active_count}\n"
        "🛡 Security: **MAXIMUM**"
    )
    bot.send_message(message.chat.id, stats, parse_mode='Markdown')

@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    if not check_admin(message): return
    msg_text = message.text.replace('/broadcast', '').strip()
    if not msg_text: return bot.reply_to(message, "Usage: `/broadcast Hi Team`")
    
    bot.send_message(ADMIN_ID, "🚀 Sending broadcast...")
    for u in users:
        try: bot.send_message(u, f"📢 **ADMIN MESSAGE:**\n\n{msg_text}")
        except: pass
    bot.send_message(ADMIN_ID, "✅ Sent to all users.")

@bot.message_handler(commands=['logs'])
def system_logs(message):
    if not check_admin(message): return
    log_msg = (
        f"📋 **LOG REPORT**\n"
        f"• Threads: {threading.active_count()}\n"
        f"• Bot Status: 🟢 Stable\n"
        f"• Version: Aditya v2.4"
    )
    bot.send_message(message.chat.id, log_msg)

print("Aditya Information Bot v2.4 is ONLINE! 🚀")
bot.infinity_polling()
