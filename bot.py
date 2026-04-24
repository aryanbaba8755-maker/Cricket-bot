import telebot
import random
import re # Yeh regex ke liye zaroori hai

# Yahan apna Token aur ID daalein
API_TOKEN = '8640082666:AAE3PUZvd07PAcN-aUJzIgK-BBhs4UTCUkY'
OWNER_ID = 7007926290  # Apni numeric ID yahan likhein

bot = telebot.TeleBot(API_TOKEN)

# Owner Check Function
def is_owner_in_group(chat_id):
    try:
        member = bot.get_chat_member(chat_id, OWNER_ID)
        if member.status in ['left', 'kicked']:
            return False
        return True
    except:
        return False

# Admin Check Function
def is_user_admin(chat_id, user_id):
    try:
        admins = bot.get_chat_administrators(chat_id)
        return any(admin.user.id == user_id for admin in admins)
    except:
        return False

# Ball Results List
cricket_outcomes = [
    "Wide ball", "Run out", "1 run", "2 run", "3 run", 
    "4 run", "6 run", "Dot ball", "No ball", "Caught out", "Bowled"
]

# /ball [number] handle karne ke liye (space ke saath)
@bot.message_handler(regexp=r'^/ball\s[1-6]$')
def handle_ball_with_space(message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    # 1. Check Owner
    if not is_owner_in_group(chat_id):
        return 

    # 2. Check Admin
    if is_user_admin(chat_id, user_id):
        outcome = random.choice(cricket_outcomes)
        bot.reply_to(message, outcome)
    else:
        bot.reply_to(message, "Sirf Admins hi yeh command use kar sakte hain")

# /toss command
@bot.message_handler(commands=['toss'])
def handle_toss(message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    if not is_owner_in_group(chat_id):
        return

    if is_user_admin(chat_id, user_id):
        toss_result = random.choice(["Heads", "Tails"])
        bot.reply_to(message, toss_result)
    else:
        bot.reply_to(message, "Sirf Admins hi yeh command use kar sakte hain")

print("Bot is running with /ball [space] number format...")
bot.infinity_polling()
