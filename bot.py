import os
import random
from telegram import Update
from telegram.ext import Application, CommandHandler, ChatMemberHandler, ContextTypes

# --- BOT CONFIGURATION ---
BOT_TOKEN = "8920375012:AAHIg9CI_07z3cAmPJQmahS7ZfhQJEGYs3M"  # Yahan apna token dalein
OWNER_ID = 2107169286
RENDER_URL = "https://cricket-bot-1-79oq.onrender.com" 
PORT = int(os.environ.get('PORT', 8000))

# --- GLOBAL STATE VARIABLES ---
toss_mode = "normal" 
match_mode = "random"
match_states = {}

# --- HELPER FUNCTIONS ---
async def is_bot_admin(bot, chat_id):
    if chat_id > 0: 
        return True
    try:
        bot_member = await bot.get_chat_member(chat_id, bot.id)
        return bot_member.status == "administrator"
    except Exception:
        return False

async def is_admin_or_owner(bot, chat_id, user_id):
    if user_id == OWNER_ID: return True
    if chat_id > 0: return False
    admins = await bot.get_chat_administrators(chat_id)
    return any(admin.user.id == user_id for admin in admins)

def get_match_state(chat_id):
    if chat_id not in match_states:
        match_states[chat_id] = {'innings': 1, 'balls': 0, 'score_1': 0, 'score_2': 0, 'target': None}
    return match_states[chat_id]

# --- COMMAND HANDLERS ---
async def toss(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    
    if not await is_bot_admin(context.bot, chat_id):
        await update.message.reply_text("Bhai, pehle mujhe is group me Admin banao, tabhi main reply karunga! 👑")
        return

    if not await is_admin_or_owner(context.bot, chat_id, user_id): return

    global toss_mode
    if toss_mode == "normal": outcome = random.choice(["Heads", "Tails"])
    elif toss_mode == "heads_60": outcome = random.choice(["Heads", "Heads", "Tails", "Heads", "Tails", "Tails", "Heads", "Heads", "Tails", "Heads"])
    elif toss_mode == "tails_60": outcome = random.choice(["Tails", "Heads", "Heads", "Tails", "Tails", "Tails", "Heads", "Tails", "Tails", "Heads"])
    elif toss_mode == "heads_100": outcome = "Heads"
    elif toss_mode == "tails_100": outcome = "Tails"
    await update.message.reply_text(outcome)

async def ball(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    
    if not await is_bot_admin(context.bot, chat_id):
        await update.message.reply_text("Bhai, pehle mujhe is group me Admin banao, tabhi main reply karunga! 👑")
        return

    if not await is_admin_or_owner(context.bot, chat_id, user_id): return

    try:
        ball_num = int(context.args[0])
        if ball_num < 1 or ball_num > 6:
            await update.message.reply_text("You should add value a number 1 to 6")
            return
    except (IndexError, ValueError):
        await update.message.reply_text("You should add value a number 1 to 6")
        return

    state = get_match_state(chat_id)
    
    outcomes = ['Dot ball', '1 run', '2 run', '3 run', '4 run', '6 run', 'Wide ball', 'No ball', 'Caught out', 'Bowled', 'Run out']
    runs_map = {'Dot ball': 0, '1 run': 1, '2 run': 2, '3 run': 3, '4 run': 4, '6 run': 6, 'Wide ball': 1, 'No ball': 1, 'Caught out': 0, 'Bowled': 0, 'Run out': 0}

    global match_mode
    chosen_outcome = "Dot ball"

    # --- ADVANCED RIGGING LOGIC ---
    if match_mode == "bat_wins":
        if state['innings'] == 1:
            weights = [10, 20, 20, 5, 20, 10, 5, 5, 2, 2, 1] 
            chosen_outcome = random.choices(outcomes, weights=weights, k=1)[0]
        elif state['innings'] == 2:
            runs_needed = state['target'] - state['score_2']
            balls_left = 6 - state['balls']
            req_rate = runs_needed / max(1, balls_left)

            if req_rate > 3: 
                weights = [0, 10, 20, 5, 30, 25, 5, 5, 0, 0, 0]
            else: 
                weights = [40, 20, 10, 0, 0, 0, 0, 0, 15, 10, 5]

            valid_outcomes, valid_weights = [], []
            for i, out in enumerate(outcomes):
                if runs_map[out] < runs_needed: 
                    valid_outcomes.append(out)
                    valid_weights.append(weights[i])

            if sum(valid_weights) == 0:
                chosen_outcome = "Dot ball"
            else:
                chosen_outcome = random.choices(valid_outcomes, weights=valid_weights, k=1)[0]

    elif match_mode == "ball_wins":
        if state['innings'] == 1:
            weights = [15, 25, 15, 5, 15, 10, 5, 5, 3, 1, 1]
            chosen_outcome = random.choices(outcomes, weights=weights, k=1)[0]
        elif state['innings'] == 2:
            runs_needed = state['target'] - state['score_2']
            balls_left = 6 - state['balls']
            req_rate = runs_needed / max(1, balls_left)

            if req_rate > 2: 
                weights = [0, 5, 15, 5, 30, 40, 0, 0, 0, 0, 0]
            elif req_rate < 1: 
                weights = [30, 30, 10, 0, 0, 0, 5, 5, 10, 5, 5]
            else:
                weights = [10, 20, 20, 5, 20, 15, 5, 5, 0, 0, 0]

            if balls_left == 1 and runs_needed > 0:
                valid_outcomes, valid_weights = [], []
                for i, out in enumerate(outcomes):
                    if runs_map[out] >= runs_needed: 
                        valid_outcomes.append(out)
                        valid_weights.append(weights[i] if weights[i] > 0 else 10)
                
                if sum(valid_weights) == 0:
                    chosen_outcome = "6 run" if runs_needed <= 6 else "No ball"
                else:
                    chosen_outcome = random.choices(valid_outcomes, weights=valid_weights, k=1)[0]
            else:
                chosen_outcome = random.choices(outcomes, weights=weights, k=1)[0]
    else:
        chosen_outcome = random.choices(outcomes, weights=[20, 30, 15, 5, 10, 5, 5, 5, 2, 2, 1], k=1)[0]


    # --- CLEAN DISPLAY LOGIC ---
    reply_text = f"0.{ball_num} ⚾ {chosen_outcome}"

    runs_scored = runs_map.get(chosen_outcome, 0)
    if state['innings'] == 1: state['score_1'] += runs_scored
    else: state['score_2'] += runs_scored

    is_extra = chosen_outcome in ['Wide ball', 'No ball']
    if not is_extra:
        state['balls'] += 1 
    
    # Target Chased Check (Reset game silently)
    if state['innings'] == 2 and state['target'] is not None and state['score_2'] >= state['target']:
        match_states[chat_id] = {'innings': 1, 'balls': 0, 'score_1': 0, 'score_2': 0, 'target': None} 
        
    # Over End Check (6 Legal Balls) - Change innings or reset game silently
    elif state['balls'] == 6:
        if state['innings'] == 1:
            state['innings'] = 2
            state['target'] = state['score_1'] + 1
            state['balls'] = 0
        elif state['innings'] == 2:
            match_states[chat_id] = {'innings': 1, 'balls': 0, 'score_1': 0, 'score_2': 0, 'target': None} 

    await update.message.reply_text(reply_text)

async def owner_modes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != OWNER_ID: return

    chat_id = update.effective_chat.id
    if not await is_bot_admin(context.bot, chat_id):
        await update.message.reply_text("Bhai, pehle mujhe is group me Admin banao, tabhi main reply karunga! 👑")
        return

    command = update.message.text.lower()
    global toss_mode, match_mode

    if '/psheadswin' in command: toss_mode = "heads_60"; await update.message.reply_text("Heads 60% Mode Active 🎯")
    elif '/rkstailswin' in command: toss_mode = "tails_60"; await update.message.reply_text("Tails 60% Mode Active 🎯")
    elif '/psonlyhead' in command: toss_mode = "heads_100"; await update.message.reply_text("Only Heads Mode Active 🪙")
    elif '/psonlytails' in command: toss_mode = "tails_100"; await update.message.reply_text("Only Tails Mode Active 🪙")
    elif '/fixthis' in command: toss_mode = "normal"; await update.message.reply_text("Random Toss Mode Active 🎲")
    elif '/pswinbat' in command: match_mode = "bat_wins"; match_states[update.effective_chat.id] = {'innings': 1, 'balls': 0, 'score_1': 0, 'score_2': 0, 'target': None}; await update.message.reply_text("Batting Team Wins Mode Active 🏏")
    elif '/psballwin' in command: match_mode = "ball_wins"; match_states[update.effective_chat.id] = {'innings': 1, 'balls': 0, 'score_1': 0, 'score_2': 0, 'target': None}; await update.message.reply_text("Chasing Team Wins Mode Active 🏏")
    elif '/psrandom' in command: match_mode = "random"; match_states[update.effective_chat.id] = {'innings': 1, 'balls': 0, 'score_1': 0, 'score_2': 0, 'target': None}; await update.message.reply_text("Random Cricket Mode Active 🎲")

async def track_chats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = update.my_chat_member
    if result.new_chat_member.status == "member":
        if result.from_user.id != OWNER_ID:
            await context.bot.leave_chat(result.chat.id)

def main():
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("toss", toss))
    application.add_handler(CommandHandler("ball", ball))
    
    owner_cmds = ["psheadswin", "rkstailswin", "fixthis", "psonlyhead", "psonlytails", "pswinbat", "psballwin", "psrandom"]
    application.add_handler(CommandHandler(owner_cmds, owner_modes))
    
    application.add_handler(ChatMemberHandler(track_chats, ChatMemberHandler.MY_CHAT_MEMBER))

    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=RENDER_URL
    )

if __name__ == '__main__':
    main()
    
