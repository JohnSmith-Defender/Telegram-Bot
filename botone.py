import asyncio
import sys

# Set the event loop policy for Windows
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import sqlite3
from datetime import datetime
import random
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, MessageHandler, CallbackQueryHandler, CommandHandler, filters, ContextTypes, ChatJoinRequestHandler

# Emojis and welcome messages
emojis = ['🗡', '🌡', '🛡', '👌', '🪙', '😎', '👾', '📀', '😡', '🖥', '💀']
welcome_images = ['./image/1.png', './image/2.png', './image/3.png', './image/4.png', './image/5.png', './image/6.png', './image/7.png', './image/8.png', './image/9.png', './image/10.png']
welcome_texts = ["Welcome to the group!", "Hello, enjoy your stay!", "Great to see you here!", "Glad to have you with us!", "Cheers to a great experience!", "You're in the right place!", "Enjoy!", "You're welcome!", "Happy to have you here!", "Let's make memories!"]

# Connect to SQLite database
conn = sqlite3.connect('bot_database.db', check_same_thread=False)
c = conn.cursor()

# Create a table to store user data
c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        userName TEXT,
        referCount INTEGER DEFAULT 0,
        referer INTEGER,
        joinedTime TEXT,
        verified BOOLEAN DEFAULT 0,
        currentViolatePoint INTEGER DEFAULT 0,
        referLink TEXT
    )
''')
conn.commit()

# Helper functions for database operations
def execute_query(query, params=()):
    """Executes a query and commits changes if needed."""
    c.execute(query, params)
    conn.commit()

def fetch_query(query, params=()):
    """Executes a query and fetches results."""
    c.execute(query, params)
    return c.fetchall()

def fetch_one_query(query, params=()):
    """Executes a query and fetches a single result."""
    c.execute(query, params)
    return c.fetchone()

# Start verification process
async def start_verification(user_id, username, update, context):
    emoji_list = random.sample(emojis, len(emojis))
    correct_emoji = random.choice(emoji_list)
    context.bot_data[user_id] = {'correct_emoji': correct_emoji, 'attempts': 0}

    buttons = [[InlineKeyboardButton(emoji, callback_data=f"{user_id}:{emoji}")] for emoji in emoji_list]
    reply_markup = InlineKeyboardMarkup(buttons)

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Hi @{username}! 🎉\nSelect the correct emoji to verify you're human. {correct_emoji}",
        reply_markup=reply_markup
    )

# Send a welcome message with a random image and greeting
async def send_welcome_message(update, context):
    selected_image = random.choice(welcome_images)
    selected_text = random.choice(welcome_texts)

    await context.bot.send_photo(
        chat_id=update.effective_chat.id,
        photo=open(selected_image, 'rb'),
        caption=selected_text
    )

# Check and update referrer if applicable
def check_and_update_referer(refer_link):
    refer_link = fetch_one_query('UPDATE users SET referCount = referCount + 1 WHERE referLink = ?', (refer_link,))

# Handle verification button clicks
async def handle_button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user_id, selected_emoji = data.split(':')
    user_id = int(user_id)

    user_data = context.bot_data.get(user_id)
    correct_emoji = user_data['correct_emoji']
    attempts = user_data['attempts']

    if selected_emoji == correct_emoji:
        execute_query('UPDATE users SET verified = 1 WHERE user_id = ?', (user_id,))
        check_and_update_referer(user_id)
        await send_welcome_message(update, context)
        await query.answer(text="✅ Correct! You are verified!")
    else:
        attempts += 1
        context.bot_data[user_id]['attempts'] = attempts
        if attempts >= 3:
            await handle_violation(user_id, query, context)
        else:
            await query.answer(text=f"❌ Wrong! You have {3 - attempts} attempt(s) left.")

# Handle violations and ban user if needed
async def handle_violation(user_id, query, context):
    execute_query('UPDATE users SET currentViolatePoint = currentViolatePoint + 1 WHERE user_id = ?', (user_id,))
    violation_count = fetch_one_query('SELECT currentViolatePoint FROM users WHERE user_id = ?', (user_id,))[0]

    if violation_count >= 3:
        await context.bot.ban_chat_member(chat_id=query.message.chat_id, user_id=user_id)
        await query.answer(text="❌ You failed 3 times. You are now banned.")
    else:
        await query.answer(text=f"❌ Wrong! You have {3 - violation_count} violation(s) left.")

# Handle new user join event using MessageHandler
async def handle_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # For each new member
    for new_member in update.message.new_chat_members:
        user_id = new_member.id
        username = new_member.username if new_member.username else new_member.full_name
        chat_id = update.message.chat.id

        # Start the verification process
        await start_verification(user_id, username, update, context)

        # Notify the group that the user has joined and is undergoing verification
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"Welcome @{username}! Please complete the verification process to stay in the group."
        )

async def handle_join_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    join_request = update.chat_join_request
    user_id = join_request.from_user.id
    username = join_request.from_user.username

    # Check if the user joined using a referral link
    if join_request.invite_link:
        refer_link = join_request.invite_link.invite_link  # Get the invite link they used
    
    # Create a unique referral link for the user
        chat_id = update.effective_chat.id
        invite_link = await context.bot.create_chat_invite_link(chat_id, name=f"Referral-{username}")

    execute_query('''
        INSERT OR REPLACE INTO users (user_id, userName, joinedTime, referLink)
        VALUES (?, ?, ?, ?)
    ''', (user_id, username, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), invite_link.invite_link))

    check_and_update_referer(refer_link)

    # Approve the join request
    await context.bot.approve_chat_join_request(chat_id=join_request.chat.id, user_id=user_id)

# Check messages to prevent unverified users from sending messages
async def check_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    result = fetch_one_query('SELECT verified, currentViolatePoint FROM users WHERE user_id = ?', (user_id,))

    if result and result[0] == 1:
        return
    else:
        await handle_violation(user_id, update.message, context)
        await update.message.delete()

# Show top 10 referrers
async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    top_referrers = fetch_query('''
        SELECT userName, referCount 
        FROM users 
        ORDER BY referCount DESC 
        LIMIT 10
    ''')

    leaderboard_message = "🏆 Top 10 Referrers 🏆\n\n"
    for rank, (username, refer_count) in enumerate(top_referrers, 1):
        leaderboard_message += f"{rank}. @{username}: {refer_count} referrals\n"

    await context.bot.send_message(chat_id=update.effective_chat.id, text=leaderboard_message)

# Show all data, admin-only
async def referdata(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    admins = await context.bot.get_chat_administrators(chat_id)

    if user_id not in [admin.user.id for admin in admins]:
        await update.message.reply_text("❌ You do not have permission to use this command.")
        return

    all_data = fetch_query('SELECT * FROM users')

    referdata_message = "📋 User Data 📋\n\n"
    for user in all_data:
        referdata_message += (f"UserID: {user[0]}, Username: {user[1]}, "
                              f"Referrals: {user[2]}, RefererID: {user[3]}, "
                              f"Joined: {user[4]}, Verified: {user[5]}, "
                              f"Violations: {user[6]}, Refer Link: {user[7]}\n")

    await context.bot.send_message(chat_id=user_id, text=referdata_message)

# Function to handle /myreferlink command
async def myreferlink(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username

    # Check if the user already has a referral link in the database
    refer_link = fetch_one_query('SELECT referLink FROM users WHERE user_id = ?', (user_id,))

    # If the user does not have a referral link, create a new one
    if not refer_link or refer_link[0] is None:
        chat_id = update.effective_chat.id
        invite_link = await context.bot.create_chat_invite_link(chat_id, name=f"Referral-{username}", creates_join_request=True)

        # Store the invite link in the database
        execute_query('UPDATE users SET referLink = ? WHERE user_id = ?', (invite_link.invite_link, user_id))

        refer_link = invite_link.invite_link
    else:
        refer_link = refer_link[0]  # Extract the existing link from the tuple

    # Send the user's referral link as a message
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Hi @{username}! 🎉 Here is your unique referral link: {refer_link}\n"
             "Share this link to invite others and earn referral rewards!"
    )

if __name__ == "__main__":
    application = ApplicationBuilder().token("7659170454:AAFVNsxH_MnodcczfCaJYEZUuMlXBnKAskg").build()

    # Add handlers
    application.add_handler(CallbackQueryHandler(handle_button_click))
    application.add_handler(ChatJoinRequestHandler(handle_join_request))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), check_message))
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, handle_new_member))
    application.add_handler(CommandHandler('leaderboard', leaderboard))
    application.add_handler(CommandHandler('referdata', referdata))
    application.add_handler(CommandHandler('myreferlink', myreferlink))

    # Start polling for updates from Telegram
    application.run_polling()
