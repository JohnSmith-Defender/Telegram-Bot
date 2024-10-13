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
emojis = ['👍','🍀','🕶','🎃','🐳','😈','👽','👻','🍼','🥔']
welcome_images = ['./image/1.png', './image/2.png', './image/3.png', './image/4.png', './image/5.png']
welcome_texts = [
    "🕯️ Welcome to the journey, traveler! 🕯️\n\nYour adventure in HAUNTED LAND begins right here in our Telegram Group! 🌕 This is the first step on a path that will take you through mysterious places like Dungannon, Travercraig, Pine Barrens, and beyond. 🌲🏰 Are you ready to explore the unknown?\n\nFor the latest news and updates, don’t forget to join our Official Announcement Channel! Stay connected with us on [X](https://x.com/haunted_land) and [Instagram](https://www.instagram.com/hauntedland) to keep up with everything happening in The Land. 🌑✨",
    
    "🕯️ Prepare for an unforgettable adventure in HAUNTED LAND! 🕯️\n\nThis journey is filled with surprises around every corner! 🌑 From the epic battles to the mysterious creatures, HAUNTED LAND will keep you on the edge of your seat. With engaging features, powerful allies, and plenty of hidden secrets, you’ll be drawn deeper into the lore of this mystical land. 🌍🔮\n\nKeep up with all the exciting surprises and adventures ahead by following us on [X](https://x.com/haunted_land), [Instagram](https://www.instagram.com/hauntedland), and explore more in-depth details on our [Medium](https://hauntedland.medium.com/)! 🚀✨",
    
    "🕯️ Welcome to the future of gaming with HAUNTED LAND! 🕯️\n\nOur upcoming AAA Game is set to push the boundaries of technology. 🌐 Utilizing the latest in NFT integration, Photorealistic Graphics, and powered by Unreal Engine, it supports VR/AR technologies for an immersive experience like no other. 🔮 Get ready to dive into a world enhanced with MMORPG characteristics, where your journey will be as real as it gets! 🎮🚀\n\nStay connected with the latest updates on our [X](https://x.com/haunted_land), [Instagram](https://www.instagram.com/hauntedland), and dive into more details on our [Medium](https://hauntedland.medium.com/). 🌑✨",
    
    "🕯️ Greetings, brave soul, and welcome to the world of HAUNTED LAND 🕯️\n\nWhile many things are brewing in our universe—including our Telegram Mini App Game, there is something far more colossal being built behind the scenes... our AAA Game! 🏰💀 From powerful weapons to ancient potions, every detail is crafted with care. Want to dive into the secrets? Uncover everything from blueprints to PDFs on our [Medium](https://hauntedland.medium.com/). 🧙‍♂️✨\n\nStay connected with us on [X](https://x.com/haunted_land) and [Instagram](https://www.instagram.com/hauntedland) for the latest updates! 🚀",
    
    "🕯️ Welcome to the vast and mysterious world of HAUNTED LAND! 🕯️\n\nThis isn’t just another game—it’s an epic adventure where crypto and gaming truly unite for a one-of-a-kind experience. 🌍💀 From exploring ancient lands to battling fearsome creatures, HAUNTED LAND offers immersive gameplay like no other. 🏹💥 With the power of NFTs and blockchain technology, your journey in The Land will be full of real stakes, real rewards, and real fun!\n\nStay ahead of the adventure by following us on [X](https://x.com/haunted_land), [Instagram](https://www.instagram.com/hauntedland), and dive deeper into the HAUNTED LAND universe on our [Medium](https://hauntedland.medium.com/)! 🚀✨"
]

cur_member_index = 0
random_index = 0


# Connect to SQLite database
conn = sqlite3.connect('bot_database.db', check_same_thread=False)
c = conn.cursor()

# Create a table to store user data
c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        userName TEXT,
        referCount INTEGER DEFAULT 0,
        referer INTEGER DEFAULT NULL,
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
async def start_verification(user_id, username, update, context:ContextTypes.DEFAULT_TYPE):
    emoji_list = random.sample(emojis, len(emojis))
    correct_emoji = random.choice(emoji_list)
    context.bot_data[user_id] = {'correct_emoji': correct_emoji, 'attempts': 0, 'emoji_list':emoji_list}

    # Arrange emojis in two rows, 5 per row
    buttons = [
        [
            InlineKeyboardButton(emoji, callback_data=f"{user_id}:{emoji}")
            for emoji in emoji_list[i:i+5]
        ]
        for i in range(0, len(emoji_list), 5)
    ]
    # Add a "Verify" button at the bottom
    buttons.append([InlineKeyboardButton("✅ Verify", callback_data=f"{user_id}:verify")])
    
    reply_markup = InlineKeyboardMarkup(buttons)

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"""🕯️ Welcome, traveler! 🕯️
I am Edgar, the gatekeeper of HAUNTED LAND. To walk among the shadows of our forbidden order, you must first prove you're not a ghoul! 🧟‍♂️ The first step is simple: choose the right emoji, and reveal your true self. 🧠Your answer awaits with: {correct_emoji}.
    
Don’t forget to follow us on X for all the latest updates 
👉 [HAUNTED LAND on X](https://x.com/haunted_land) and explore deeper secrets on our Medium 👉 [HAUNTED LAND Medium](https://hauntedland.medium.com).
Step carefully… 🌑✨""",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

# Send a welcome message with a random image and greeting
async def send_welcome_message(update, context):
    global cur_member_index
    global random_index
    if cur_member_index % 3 == 0:
        random_index = random.randint(0, len(welcome_texts) - 1)
        selected_image = welcome_images[random_index]
    cur_member_index = cur_member_index + 1
    selected_text = welcome_texts[random_index]

    await context.bot.send_photo(
        chat_id=update.effective_chat.id,
        photo=open(selected_image, 'rb'),
        caption=selected_text,
        parse_mode="Markdown"
    )

# Check and update referrer if applicable
def check_and_update_referer(refer_link):
    refer_link = fetch_one_query('UPDATE users SET referCount = referCount + 1 WHERE referLink = ?', (refer_link,))

# Handle verification button clicks
async def handle_button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id, data = query.data.split(':')
    user_id = int(user_id)

    # Get the original message sent for verification
    verification_message = query.message

    if data == "verify":
        # Handle the verification process
        user_data = context.bot_data.get(user_id, {})
        selected_emoji = user_data.get('selected_emoji')
        correct_emoji = user_data.get('correct_emoji')
        attempts = user_data['attempts']
        if selected_emoji:
            if selected_emoji == correct_emoji:
                execute_query('UPDATE users SET verified = 1 WHERE user_id = ?', (user_id,))
                check_and_update_referer(user_id)
                # Delete the verification message
                await context.bot.delete_message(chat_id=verification_message.chat.id, message_id=verification_message.message_id)
                await query.answer(text="✅ Correct! You are verified!")
                await send_welcome_message(update, context)
            else:
                attempts += 1
                context.bot_data[user_id]['attempts'] = attempts
                if attempts >= 3:
                    await handle_violation(user_id, query, context)
                else:
                    await query.answer(text=f"❌ Wrong! You have {3 - attempts} attempt(s) left.")
        else:
            await query.answer("Please select an emoji before verifying.", show_alert=True)
    else:
        # Handle emoji selection
        context.bot_data[int(user_id)]['selected_emoji'] = data
        emoji_list = context.bot_data[int(user_id)]['emoji_list']

        # Update buttons to show the selected emoji with a tick (✓)
        buttons = [
            [
                InlineKeyboardButton(f"{emoji} {'✓' if emoji == data else ''}", callback_data=f"{user_id}:{emoji}")
                for emoji in emoji_list[i:i+5]
            ]
            for i in range(0, len(emoji_list), 5)
        ]
        buttons.append([InlineKeyboardButton("✅ Verify", callback_data=f"{user_id}:verify")])

        reply_markup = InlineKeyboardMarkup(buttons)

        await query.edit_message_reply_markup(reply_markup=reply_markup)

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

        # Start the verification process
        await start_verification(user_id, username, update, context)

async def handle_join_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    join_request = update.chat_join_request
    user_id = join_request.from_user.id
    username = join_request.from_user.username
    refer_link_val = None
    referer_id = None

    print('here!')

    # Check if the user joined using a referral link
    if join_request.invite_link:
        refer_link = join_request.invite_link.invite_link  # Get the invite link they used
        # Find the referer_id using the refer_link
        referer_id = fetch_one_query('SELECT user_id FROM users WHERE referLink = ?', (refer_link,))
    
    # Create a unique referral link for the user
    chat_id = update.effective_chat.id
    invite_link = await context.bot.create_chat_invite_link(chat_id, name=f"Referral-{username}")
    refer_link_val = invite_link.invite_link

    referer_id = fetch_one_query()


    execute_query('''
        INSERT OR REPLACE INTO users (user_id, userName, joinedTime, referLink, referer)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, username, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), refer_link_val, referer_id))

    check_and_update_referer(refer_link)

    # Approve the join request
    await context.bot.approve_chat_join_request(chat_id=join_request.chat.id, user_id=user_id)

async def handle_user_leave(update: Update, context: ContextTypes.DEFAULT_TYPE):
    member = update.message.left_chat_member
    user_id = member.id
    
    # Find the referrer ID for the user who left
    referer = fetch_one_query('SELECT referer FROM users WHERE user_id = ?', (user_id,))
    
    if referer and referer[0] is not None:
        referer_id = referer[0]  # Get the referrer ID

        # Decrement the referrer’s count
        execute_query('UPDATE users SET referCount = referCount - 1 WHERE user_id = ?', (referer_id,))
        print(f'Decremented referer ID: {referer_id}, New count: {fetch_one_query("SELECT referCount FROM users WHERE user_id = ?", (referer_id,))[0]}')

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
    user_id = update.effective_user.id
    top_referrers = fetch_query('''
        SELECT userName, referCount 
        FROM users 
        ORDER BY referCount DESC 
        LIMIT 10
    ''')

     # Fetch the user's referral count
    user_refer_count = fetch_one_query('SELECT referCount FROM users WHERE user_id = ?', (user_id,))

    leaderboard_message = "🏆 Top 10 Referrers 🏆\n\n"
    for rank, (username, refer_count) in enumerate(top_referrers, 1):
        leaderboard_message += f"{rank}. @{username}: {refer_count} referrals\n"

     # Add the user's referral count to the message
    if user_refer_count:
        leaderboard_message += f"\nYour referral count: {user_refer_count[0]}"

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
        
        execute_query('''
        INSERT OR REPLACE INTO users (user_id, userName, joinedTime, referLink)
        VALUES (?, ?, ?, ?)
    ''', (user_id, username, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), invite_link.invite_link))

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
    application = ApplicationBuilder().token("7747378673:AAFlj07rCmCJQkcqEYpkVJ5ZtVujkq54zxI").build()

    # Add handlers
    application.add_handler(CallbackQueryHandler(handle_button_click))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), check_message))
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, handle_new_member))
    application.add_handler(CommandHandler('leaderboard', leaderboard))
    application.add_handler(CommandHandler('referdata', referdata))
    application.add_handler(CommandHandler('myreferlink', myreferlink))
    application.add_handler(ChatJoinRequestHandler(handle_join_request))
    application.add_handler(MessageHandler(filters.StatusUpdate.LEFT_CHAT_MEMBER, handle_user_leave))

    # Start polling for updates from Telegram
    application.run_polling()
