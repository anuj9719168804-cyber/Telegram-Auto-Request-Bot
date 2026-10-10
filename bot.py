import os
from html import escape as h
import json
import logging
import asyncio
import re
import random
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

BOT_TOKEN = os.getenv('BOT_TOKEN')
OWNER_ID = int(os.getenv('OWNER_ID', '0'))  # Add owner ID in .env

if not BOT_TOKEN:
    raise RuntimeError('⚠️ BOT_TOKEN not set in .env')

# Session credentials
API_ID = int(os.getenv('API_ID', '0'))
API_HASH = os.getenv('API_HASH', '')

DATA_DIR = Path('data')
DATA_DIR.mkdir(exist_ok=True)

ACCEPTED_FN = DATA_DIR / 'accepted_users.json'
GROUPS_FN = DATA_DIR / 'groups.json'
LIMITS_FN = DATA_DIR / 'limits.json'
SESSIONS_FN = DATA_DIR / 'sessions.json'

CATBOX_VIDEO_URL = 'https://files.catbox.moe/kg7jcs.mp4'

# Welcome pictures: one is picked at random for every /start
PICS = (
    "https://img3.teletype.in/files/67/73/67735f4f-933a-41d9-86b9-609fa03b6614.jpeg",
    "https://img3.teletype.in/files/a6/b6/a6b666ef-afa0-4793-bd6b-235265258840.jpeg",
    "https://img3.teletype.in/files/e8/01/e8013193-9299-4cdc-8222-f4e3801a05e8.jpeg",
    "https://img4.teletype.in/files/77/7f/777f2c2d-fa53-4298-9dee-ab39d9bddf81.jpeg",
    "https://img3.teletype.in/files/a1/9e/a19e9352-dfee-471a-ae3f-14eb2e1b975b.jpeg",
    "https://img1.teletype.in/files/84/84/8484934a-a247-4b1a-8f1f-74aac621bea6.jpeg",
    "https://img4.teletype.in/files/b2/89/b289d67c-2299-4cf6-91c3-b84c83c57caa.jpeg",
    "https://img3.teletype.in/files/a0/49/a049a7b1-2924-41c1-95d4-8c466c1a80ad.jpeg",
    "https://img2.teletype.in/files/59/b3/59b3a62e-e2ce-4f00-847d-9910f0498884.jpeg",
    "https://img2.teletype.in/files/91/d8/91d8838b-85ec-45ff-868f-24d66126ce55.jpeg",
    "https://img4.teletype.in/files/71/a5/71a5481f-2398-4520-8229-222d1cf733e7.jpeg",
    "https://img4.teletype.in/files/f4/b0/f4b007ec-fc8c-49fd-a1fb-b0d02985120a.jpeg",
    "https://img4.teletype.in/files/f6/3c/f63cee0d-10ff-4b8d-9ccc-943fa80a1344.jpeg",
    "https://img4.teletype.in/files/77/ff/77ff451d-0c8a-4aeb-aa9a-a1ae7ca74069.jpeg",
    "https://img4.teletype.in/files/bb/e9/bbe9e4f6-6226-4764-8169-b7d368e29e8c.jpeg",
    "https://img2.teletype.in/files/d4/b8/d4b806a2-c534-466f-85cb-f05a9e31dc92.jpeg",
    "https://img4.teletype.in/files/b6/aa/b6aab772-1d39-4b7e-bfe5-8d04b57ac31e.jpeg",
    "https://img4.teletype.in/files/f5/c3/f5c3a05e-ecfb-4a8e-b921-2b264d40d0ce.jpeg",
    "https://img4.teletype.in/files/3f/01/3f0102af-352a-4a0a-abbd-f18919c56dc9.jpeg",
    "https://img4.teletype.in/files/7f/f2/7ff228ef-6e74-4baf-a877-b35c016d6c7b.jpeg",
    "https://img1.teletype.in/files/8b/02/8b02924e-4f24-4ace-8b3f-be2f8044b8ec.jpeg",
    "https://img2.teletype.in/files/dc/16/dc1625b2-410c-48da-98c1-1956b87768e1.jpeg",
    "https://img2.teletype.in/files/97/f3/97f31df6-2cca-4f58-8269-97aebb6d9ea7.jpeg",
    "https://img2.teletype.in/files/97/65/9765707e-1855-429b-89ba-03401b734827.jpeg",
    "https://img4.teletype.in/files/f4/53/f45390f3-e1eb-4570-9d67-c4114db18589.jpeg",
    "https://img1.teletype.in/files/81/26/81265a94-68ff-47ed-b409-fad382e7a627.jpeg",
    "https://img1.teletype.in/files/0a/1b/0a1b5f17-095c-4826-84c8-39a8b9b9deef.jpeg",
    "https://img4.teletype.in/files/f5/94/f594fbe2-b52d-489a-86c9-23b2f2dbe4d7.jpeg",
    "https://img3.teletype.in/files/e3/76/e376be29-065b-4c1a-986d-aba69d08208f.jpeg",
    "https://img1.teletype.in/files/8f/e6/8fe67878-43a3-4b3d-851f-63727a6a2b0b.jpeg",
    "https://img2.teletype.in/files/1a/d3/1ad3fa24-c3bf-4ca8-a7ef-a79286b1e37c.jpeg",
    "https://img1.teletype.in/files/80/1a/801a77ad-bf05-4d7a-96c9-2b1cde09d04f.jpeg",
    "https://img4.teletype.in/files/f4/b0/f4b007ec-fc8c-49fd-a1fb-b0d02985120a.jpeg",
    "https://img4.teletype.in/files/f6/3c/f63cee0d-10ff-4b8d-9ccc-943fa80a1344.jpeg",
    "https://ik.imagekit.io/jbxs2z512/naruto_GxcPgSeOy.jpg?updatedAt=1748486799631",
    "https://ik.imagekit.io/jbxs2z512/hd-anime-prr1y1k5gqxfcgpv.jpg?updatedAt=1748487947183",
    "https://ik.imagekit.io/jbxs2z512/dazai-osamu-sunset-rooftop-anime-wallpaper-cover.jpg?updatedAt=1748488276069",
    "https://ik.imagekit.io/jbxs2z512/thumb-1920-736461.png?updatedAt=1748488419323",
    "https://ik.imagekit.io/jbxs2z512/116847-3840x2160-desktop-4k-bleach-background-photo.jpg?updatedAt=1748488510841",
    "https://ik.imagekit.io/jbxs2z512/thumb-1920-1361035.jpeg?updatedAt=1748488911202",
    "https://ik.imagekit.io/jbxs2z512/thumb-1920-777955.jpg?updatedAt=1748488978230",
    "https://ik.imagekit.io/jbxs2z512/akali-wallpaper-960x540_43.jpg?updatedAt=1748489275125",
    "https://ik.imagekit.io/jbxs2z512/robin-honkai-star-rail-497@1@o?updatedAt=1748490140360",
    "https://ik.imagekit.io/jbxs2z512/wallpapersden.com_tian-guan-ci-fu_1920x1080.jpg?updatedAt=1748490255277",
    "https://ik.imagekit.io/jbxs2z512/1129176.jpg?updatedAt=1748491905419",
    "https://ik.imagekit.io/jbxs2z512/wp14288215.jpg?updatedAt=1748492348766",
    "https://ik.imagekit.io/jbxs2z512/8k-anime-girl-and-flowers-t4bj6u55nmgfdrhe.jpg?updatedAt=1748493169919",
    "https://ik.imagekit.io/jbxs2z512/anime_Fuji_Choko_princess_anime_girls_Sakura_Sakura_Woman_in_Red_mask_palace-52030.png!d?updatedAt=1748493259665",
    "https://ik.imagekit.io/jbxs2z512/1187037bb1d8aaf14a631f7b813296f1.jpg?updatedAt=1748493396756",
    "https://ik.imagekit.io/jbxs2z512/yor_forger_by_senku_07_dgifqh7-fullview.jpg_token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1cm46YXBwOjdlMGQxODg5ODIyNjQzNzNhNWYwZDQxNWVhMGQyNmUwIiwiaXNzIjoidXJuOmFwcDo3ZTBkMTg4OTgyMjY0MzczYTVmMGQ0MTVlYTBkMjZlMCIsIm9iaiI6W1t7ImhlaWdodCI6Ijw9ODAzIiwicGF0aCI6IlwvZlwvNDAxZDdlYTYtOGEyZi00ZTFiLTkxYTAtNjA3YmRlYTgzZmE4XC9kZ2lmcWg3LWNlMjY3Mzc2LWQ4NWYtNGMzZS1iNWY1LWU0OTZhYWM3ZmUyNC5wbmciLCJ3aWR0aCI6Ijw9MTI4MCJ9XV0sImF1ZCI6WyJ1cm46c2VydmljZTppbWFnZS5vcGVyYXRpb25zIl19.FVwtt0HGKv6UQqWHkEbxmE1qkI5CFNNS5SzAYj4EVUs?updatedAt=1748493490929",
    "https://ik.imagekit.io/jbxs2z512/attack-on-titan-mikasa-cover-image-ybt96t1e1041qdt3.jpg?updatedAt=1748493720903",
    "https://ik.imagekit.io/jbxs2z512/tsunade-at-her-desk-bakoh4jeg42sjn3c.jpg?updatedAt=1748493962363",
    "https://ik.imagekit.io/jbxs2z512/1b3025cb9fc1a3cd43fdff42167d0dea.jpg?updatedAt=1748498508575",
    "https://ik.imagekit.io/jbxs2z512/Fight-Break-Sphere.png?updatedAt=1750042299023",
    "https://ik.imagekit.io/jbxs2z512/doupocangqiong-medusa-queen-hd-wallpaper-preview.jpg?updatedAt=1750042397343",
    "https://ik.imagekit.io/jbxs2z512/wp5890248.jpg?updatedAt=1750042498187",
    "https://ik.imagekit.io/jbxs2z512/sacffc_uu-T1F5AC?updatedAt=1750042873876",
    "https://ik.imagekit.io/jbxs2z512/1345216.jpeg?updatedAt=1750042982858",
    "https://ik.imagekit.io/jbxs2z512/shanks-divine-departure-attack-in-one-piece-sn.jpg?updatedAt=1750043121252",
    "https://ik.imagekit.io/jbxs2z512/1a74aff1d81a1af5f3e25b9b30282e06.jpg?updatedAt=1750043251516",
    "https://ik.imagekit.io/jbxs2z512/22219.jpg?updatedAt=1751107408410",
    "https://ik.imagekit.io/jbxs2z512/21418.jpg?updatedAt=1751107452919",
    "https://ik.imagekit.io/jbxs2z512/mythical-dragon-beast-anime-style_23-2151112835.jpg?updatedAt=1751107574210",
    "https://ik.imagekit.io/jbxs2z512/halloween-scene-illustration-anime-style_23-2151794288.jpg?updatedAt=1751107676806",
    "https://ik.imagekit.io/jbxs2z512/5823589-2920x1640-desktop-hd-boy-programmer-wallpaper-image.jpg_id=1726666227?updatedAt=1751107911063",
    "https://ik.imagekit.io/jbxs2z512/thumbbig-1345576.webp?updatedAt=1751108065802",
    "https://ik.imagekit.io/jbxs2z512/thumb-440-1340473.webp?updatedAt=1751108159970",
    "https://ik.imagekit.io/jbxs2z512/wp3084738.jpg?updatedAt=1751108326075",
    "https://ik.imagekit.io/jbxs2z512/wp12362449.png?updatedAt=1751108554882",
    "https://ik.imagekit.io/jbxs2z512/wp7627005.jpg?updatedAt=1751108634878",
    "https://ik.imagekit.io/jbxs2z512/thumbbig-1335194.webp?updatedAt=1751108710765",
    "https://ik.imagekit.io/jbxs2z512/thumbbig-1373976.webp?updatedAt=1751108748746",
    "https://ik.imagekit.io/jbxs2z512/thumbbig-1065277.webp?updatedAt=1751108877871",
    "https://ik.imagekit.io/jbxs2z512/thumbbig-877141.webp?updatedAt=1751108916209",
    "https://ik.imagekit.io/jbxs2z512/thumbbig-856517.webp?updatedAt=1751108984376",
    "https://ik.imagekit.io/jbxs2z512/thumbbig-722181.webp?updatedAt=1751109016670",
    "https://ik.imagekit.io/jbxs2z512/thumbbig-1337392.webp?updatedAt=1751109084903",
    "https://ik.imagekit.io/jbxs2z512/anime-4k-pc-hd-download-wallpaper-preview%20(1).jpg?updatedAt=1751109522060",
    "https://ik.imagekit.io/jbxs2z512/876145-3840x2160-desktop-4k-konan-naruto-background-image%20(1).jpg?updatedAt=1751109523353",
    "https://ik.imagekit.io/jbxs2z512/tumblr_9663cff78634f174f81b41b64fc450df_66ebd999_1280%20(1).png?updatedAt=1751109523759",
    "https://ik.imagekit.io/jbxs2z512/anime-girl-demon-horn-art-4k-wallpaper-uhdpaper.com-714@2@b%20(1).jpg?updatedAt=1751109524369",
    "https://ik.imagekit.io/jbxs2z512/dbbb586df338d55d340ec650bcdd74fe.jpg?updatedAt=1751110984735",
    "https://ik.imagekit.io/jbxs2z512/c02aecb70c3c6a5b1f51ba09e4d2cc70.jpg?updatedAt=1751111979586",
    "https://ik.imagekit.io/jbxs2z512/6c2618a1eea58d22e2d1a5ba99c95a1c.jpg?updatedAt=1751112051082",
    "https://ik.imagekit.io/jbxs2z512/7a82750e26bf451ab1775993279e2c64.jpg?updatedAt=1751112189297",
    "https://ik.imagekit.io/jbxs2z512/a469262476f60456dd4aceb8a75deed5.jpg?updatedAt=1751112263336",
    "https://ik.imagekit.io/jbxs2z512/ad05ea75da4e9dd28f0e71c398d16a70.jpg?updatedAt=1751616664015",
    "https://ik.imagekit.io/jbxs2z512/ca525e543c2719891612c737a269d50d.jpg?updatedAt=1751616762244",
    "https://ik.imagekit.io/jbxs2z512/515329f5fb6449cd5c5742e8118912c8.jpg?updatedAt=1751616576915",
    "https://ik.imagekit.io/jbxs2z512/7d405472605913d0b1ace935591510ef.jpg?updatedAt=1751617338294",
    "https://ik.imagekit.io/jbxs2z512/e0ec0f65320e6930cfdb00a41979408c.jpg?updatedAt=1751617427686",
    "https://ik.imagekit.io/jbxs2z512/cf39f75ba7aa8391d7c32929feadaaffd7d76.jpg?updatedAt=1751617579813",
    "https://ik.imagekit.io/jbxs2z512/5f6ca554415a9626ea709f803727a267.jpg?updatedAt=1751617791661",
    "https://ik.imagekit.io/jbxs2z512/107895c50cd55d1b0bf77cc814e-00671f4.jpg?updatedAt=1751617893009",
    "https://ik.imagekit.io/jbxs2z512/4555abb8a92ccec7a37b5e3621281c77.jpg?updatedAt=1751618816270",
    "https://ik.imagekit.io/jbxs2z512/3d4aa530c4e8ef17d6098fad44728ee5.jpg?updatedAt=1751620240035",
    "https://ik.imagekit.io/jbxs2z512/2f6b6cfcd929bf97e639515a1f187f6d.jpg?updatedAt=1751620404536",
    "https://ik.imagekit.io/jbxs2z512/4f0076085b8aea935a30b9eb1c8e9867.jpg?updatedAt=1751623894659",
    "https://ik.imagekit.io/jbxs2z512/631f6026e50d6644b87bc20bca2ec12a.jpg?updatedAt=1751628298231",
    "https://ik.imagekit.io/jbxs2z512/wp15082614.jpg?updatedAt=1751628541804",
    "https://ik.imagekit.io/jbxs2z512/wp15082622.webp?updatedAt=1751628578344",
    "https://ik.imagekit.io/jbxs2z512/e618b0d2a9518326722d6483569a94c6.jpg?updatedAt=1757316947948",
    "https://ik.imagekit.io/jbxs2z512/6222c23f673d9d6b86cf759a440935d9.jpg?updatedAt=1757317031249",
    "https://ik.imagekit.io/jbxs2z512/b322fad3ae2e550b5e9a0cb1d2c78311.jpg?updatedAt=1757317116796",
    "https://ik.imagekit.io/jbxs2z512/0a7f44752689424fd901b220aa5c5516.jpg?updatedAt=1757317197691",
    "https://ik.imagekit.io/jbxs2z512/c4567ce2326aa09a4b33b0ff21e9d1ef.jpg?updatedAt=1757317301147",
    "https://ik.imagekit.io/jbxs2z512/a6a2b0fe748ec78ead3c3ac85b1472a8.jpg?updatedAt=1757317366150",
    "https://ik.imagekit.io/jbxs2z512/5763d2e3681540671e85066a5f600cf5.jpg?updatedAt=1757317432437",
    "https://ik.imagekit.io/jbxs2z512/57b6e9637bd6cf48649b4576baf72f72.jpg?updatedAt=1757317509952",
    "https://ik.imagekit.io/jbxs2z512/42e36ef6930669ea1a1696f6e2e9084c.jpg?updatedAt=1757317644096",
    "https://ik.imagekit.io/jbxs2z512/a1a4cf3066e20b9699a987e1b0379565.jpg?updatedAt=1757318914589",
    "https://ik.imagekit.io/jbxs2z512/3f36f010cb6acb9468951d561fc01464.jpg?updatedAt=1757318940586",
    "https://ik.imagekit.io/jbxs2z512/0248823b46df5e7f74b7101c305de13d.jpg?updatedAt=1757318960094",
    "https://ik.imagekit.io/jbxs2z512/62d47644f5f720b9108c0ff448dad10e.jpg?updatedAt=1757321226076",
)


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
        kb = await get_welcome_kb()
        pic = random.choice(PICS)
        try:
            await bot.send_photo(
                chat_id=user_id,
                photo=pic,
                caption=WELCOME_TEXT,
                reply_markup=kb,
                parse_mode=ParseMode.HTML,
            )
        except Exception as e:
            # Some image hosts/formats are rejected by Telegram; still send the welcome text
            logging.warning(f"Welcome photo failed ({pic}): {e}")
            await bot.send_message(
                chat_id=user_id,
                text=WELCOME_TEXT,
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
                f"✅ <b>Code sent to {h(phone_number)}</b>\n\n"
                "🔐 <b>Send the OTP code you received from Telegram</b>\n\n"
                "⚠️ <b>Send only the numbers</b>\n"
                "📝 Example: if OTP is 12345, send <code>12345</code>\n\n"
                "/cancel - cancel this process\n\n"
                "👨🏻‍💻 Dev : <a href='https://t.me/anujedits76'>Anuj Kumar</a>",
                parse_mode=ParseMode.HTML
            )
        except TelegramBadRequest:
            await bot.send_message(
                uid,
                f"✅ <b>Code sent to {h(phone_number)}</b>\n\n"
                "🔐 <b>Send the OTP code you received from Telegram</b>\n\n"
                "⚠️ <b>Send only the numbers</b>\n"
                "📝 Example: if OTP is 12345, send <code>12345</code>\n\n"
                "/cancel - cancel this process\n\n"
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
    code = msg.text.strip().replace(' ', '').replace('-', '')

    if not code.isdigit():
        await msg.answer(
            "❌ Only numbers allowed!\n\n"
            "📝 Example: 12345",
            parse_mode=None
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
                "🔒 <b>Two-Step Verification</b>\n\n"
                "Your account has 2FA enabled. Send your password.\n\n"
                "⚠️ <b>Important:</b> your password is case-sensitive\n\n"
                "/cancel - cancel this process\n\n"
                "👨🏻‍💻 Dev : <a href='https://t.me/anujedits76'>Anuj Kumar</a>",
                parse_mode=ParseMode.HTML
            )
            
        except PhoneCodeInvalidError:
            session_info['otp_attempts'] = session_info.get('otp_attempts', 0) + 1
            left = 3 - session_info['otp_attempts']
            if left > 0:
                await status_msg.edit_text(
                    "❌ <b>Invalid OTP code! Please try again.</b>\n\n"
                    f"🔄 Remaining attempts: {left}\n\n"
                    "📝 Example: 12345\n\n"
                    "/cancel - cancel this process\n\n"
                    "👨🏻‍💻 Dev : <a href='https://t.me/anujedits76'>Anuj Kumar</a>",
                    parse_mode=ParseMode.HTML
                )
            else:
                await _disconnect_login(uid)
                await state.clear()
                await status_msg.edit_text(
                    "❌ Maximum attempts reached! Process cancelled.\n\n"
                    "Please try again later with /login.",
                    parse_mode=None
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
    password = msg.text.strip()
    
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
        session_info['pwd_attempts'] = session_info.get('pwd_attempts', 0) + 1
        left = 2 - session_info['pwd_attempts']
        if left > 0:
            await status_msg.edit_text(
                "❌ <b>Invalid password! Please try again.</b>\n\n"
                f"🔄 Remaining attempts: {left}\n\n"
                "If you forgot your password, /cancel and restart with /login\n\n"
                "👨🏻‍💻 Dev : <a href='https://t.me/anujedits76'>Anuj Kumar</a>",
                parse_mode=ParseMode.HTML
            )
        else:
            await _disconnect_login(uid)
            await state.clear()
            await status_msg.edit_text(
                "❌ Maximum password attempts reached! Process cancelled.\n\n"
                "Please try again later with /login.",
                parse_mode=None
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
    "├─ <code>12345</code> — OTP verification (numbers only)\n"
    "└─ <code>your_password</code> — 2FA password\n"
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


async def start_health_server():
    """Render (and similar hosts) need a web service to listen on $PORT.
    This tiny HTTP server only answers health checks; the bot keeps polling."""
    port = os.getenv('PORT')
    if not port:
        return  # Not on a web-port host (VPS, Docker, worker): nothing to do
    from aiohttp import web

    async def health(_request):
        return web.Response(text="AK Auto Request Bot is running")

    app = web.Application()
    app.router.add_get('/', health)
    app.router.add_get('/health', health)
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', int(port)).start()
    logging.info(f"Health server listening on port {port}")

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
    
    await start_health_server()
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
