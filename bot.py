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
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, FSInputFile, ChatPermissions
import time
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

BOT_TOKEN = '8719198691:AAHmEJ_7khOIdXRYEJJJaZ-kwt8xjeAZ82Q'  # hardcoded
OWNER_ID = 8729304171  # Owner Telegram user ID (hardcoded)

if not BOT_TOKEN:
    raise RuntimeError('⚠️ BOT_TOKEN not set in .env')

# Session credentials
API_ID = 33029767  # hardcoded
API_HASH = '5d897bed11bc8b062a12f6c1c3c5360a'  # hardcoded

DATA_DIR = Path('data')
DATA_DIR.mkdir(exist_ok=True)

ACCEPTED_FN = DATA_DIR / 'accepted_users.json'
GROUPS_FN = DATA_DIR / 'groups.json'
LIMITS_FN = DATA_DIR / 'limits.json'
SESSIONS_FN = DATA_DIR / 'sessions.json'


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

# ---------- Storage: MongoDB if MONGO_URI is set, otherwise JSON files in data/ ----------
MONGO_URI = os.getenv('MONGO_URI', '')
_mongo_kv = None
if MONGO_URI:
    try:
        from pymongo import MongoClient
        _mongo_kv = MongoClient(MONGO_URI, serverSelectionTimeoutMS=8000)['spidey_bot']['kv']
        _mongo_kv.find_one({'_id': '__ping__'})
        logging.info('MongoDB storage enabled')
    except Exception as e:
        logging.error(f'MongoDB unavailable, falling back to JSON files: {e}')
        _mongo_kv = None

def load_json(path: Path, default=None):
    if _mongo_kv is not None:
        doc = _mongo_kv.find_one({'_id': Path(path).name})
        if doc is not None:
            return doc.get('data')
        return default if default is not None else {}
    if not path.exists():
        path.write_text(json.dumps(default or {}, indent=2))
    return json.loads(path.read_text())

def save_json(path: Path, data):
    if _mongo_kv is not None:
        name = Path(path).name
        _mongo_kv.replace_one({'_id': name}, {'_id': name, 'data': data}, upsert=True)
        return
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

WELCOME_BODY = (
    "<blockquote>{desc}</blockquote>\n\n"
    "≡ <b>{maint}</b> | <a href=\"https://t.me/anujedits76\">Anuj Kumar</a>"
)
WELCOME_DESC = (
    "Auto-approve join requests in your groups and channels.\n"
    "Add me as admin and give Add members / Invite users permission."
)

def build_welcome_text(first_name: str) -> str:
    return (
        f"<b>{to_small_caps('hello')} {h(first_name)}! 👋</b>\n\n"
        + WELCOME_BODY.format(desc=h(WELCOME_DESC), maint=to_small_caps('maintained by'))
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
        [make_button('➕ ADD ME TO YOUR GROUP ➕', url=f'https://t.me/{username}?startgroup=true', style=BTN_SUCCESS)],
        [make_button('ABOUT', callback_data='wel:about', style=BTN_PRIMARY),
         make_button('HELP', callback_data='wel:help', style=BTN_PRIMARY)],
        [make_button('➕ ADD ME TO YOUR CHANNEL ➕', url=f'https://t.me/{username}?startchannel=start', style=BTN_SUCCESS)],
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
    if evt.new_chat_member.status == ChatMemberStatus.ADMINISTRATOR and evt.chat.type != ChatType.PRIVATE:
        try:
            await bot.send_message(OWNER_ID, f"🎉 I am now admin in <b>{h(evt.chat.title or str(evt.chat.id))}</b> (<code>{evt.chat.id}</code>).",
                                   parse_mode=ParseMode.HTML)
        except Exception as e:
            logging.warning(f"Owner admin-notice failed: {e}")

_background_tasks = set()

QUOTES = (
    "Small steps every day lead to big results.",
    "Consistency beats talent when talent does not show up.",
    "Start where you are, use what you have, do what you can.",
    "The best time to plant a tree was twenty years ago. The second best is now.",
    "Discipline is choosing what you want most over what you want now.",
    "Done is better than perfect.",
    "Your future is built by what you do today.",
    "Stay curious, stay kind, keep building.",
    "Every expert was once a beginner.",
    "Little by little, a little becomes a lot.",
)

def send_welcome_to_user(user_id: int):
    async def _send():
        kb = await get_welcome_kb()
        pic = random.choice(PICS)
        try:
            first = (await bot.get_chat(user_id)).first_name or "there"
        except Exception:
            first = "there"
        caption = build_welcome_text(first)
        try:
            await bot.send_photo(
                chat_id=user_id,
                photo=pic,
                caption=caption,
                reply_markup=kb,
                parse_mode=ParseMode.HTML,
            )
        except Exception as e:
            # Some image hosts/formats are rejected by Telegram; still send the welcome text
            logging.warning(f"Welcome photo failed ({pic}): {e}")
            await bot.send_message(
                chat_id=user_id,
                text=caption,
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
    touch_user(uid)
    if not await is_member_of_channel(uid):
        await msg.answer(
            "❌ You must join our channel to use this bot.\n"
            "Please join first and then try again.",
            parse_mode=None,
        )
        return
    
    if await block_if_not_joined(msg):
        return
    
    if uid not in accepted_users:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [make_button('✅ Accept & Continue', callback_data='accept_privacy', style=BTN_SUCCESS)]
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
    
    if await block_if_not_joined(msg):
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
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[make_button("❌ Cancel Login", callback_data="login_cancel", style=BTN_DANGER)]])
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
                f"✅ <b>{to_small_caps('code sent to')} {h(phone_number)}</b>\n\n"
                f"<b>🔐 {to_small_caps('send the otp code you received from telegram')}</b>\n"
                f"📝 {to_small_caps('example: if otp is 12345, send')} <code>12345</code>\n\n"
                f"<b>⚠️ {to_small_caps('important: send only the numbers')}</b>\n\n"
                f"/cancel - {to_small_caps('cancel this process')}\n\n"
                "👨🏻‍💻 Dev : <a href='https://t.me/anujedits76'>Anuj Kumar</a>",
                parse_mode=ParseMode.HTML
            )
        except TelegramBadRequest:
            await bot.send_message(
                uid,
                f"✅ <b>{to_small_caps('code sent to')} {h(phone_number)}</b>\n\n"
                f"<b>🔐 {to_small_caps('send the otp code you received from telegram')}</b>\n"
                f"📝 {to_small_caps('example: if otp is 12345, send')} <code>12345</code>\n\n"
                f"<b>⚠️ {to_small_caps('important: send only the numbers')}</b>\n\n"
                f"/cancel - {to_small_caps('cancel this process')}\n\n"
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

def to_small_caps(text: str) -> str:
    """Unicode small caps, same style as the reference project"""
    normal = "abcdefghijklmnopqrstuvwxyz"
    small = "ᴀʙᴄᴅᴇғɢʜɪᴊᴋʟᴍɴᴏᴘǫʀsᴛᴜᴠᴡxʏᴢ"
    return text.translate(str.maketrans(normal + normal.upper(), small + small))

# How long an OTP stays usable in this bot (Telegram codes expire in a few minutes)
CODE_VALID_SECONDS = 300

@dp.message(LoginStates.waiting_for_code)
async def process_verification_code(msg: types.Message, state: FSMContext):
    """Process OTP verification code"""
    uid = msg.from_user.id
    code = msg.text.strip().replace(' ', '').replace('-', '')

    if not code.isdigit():
        await msg.answer(
            f"❌ <b>{to_small_caps('only numbers allowed!')}</b>\n\n"
            f"📝 {to_small_caps('example')}: 12345",
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
    if (datetime.now(timezone.utc).timestamp() - sent_at) > CODE_VALID_SECONDS:
        client = session_info.get('client')
        if client:
            try:
                await client.disconnect()
            except:
                pass
        active_login_sessions.pop(uid, None)
        await msg.answer(
            f"❌ <b>{to_small_caps('code expired')}</b>\n\n"
            f"{to_small_caps('more than 5 minutes passed. please start again with /login and send the otp quickly.')}",
            parse_mode=None
        )
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
                f"🔒 <b>{to_small_caps('your account has 2fa enabled. send your password')}</b>\n\n"
                f"⚠️ <b>{to_small_caps('important: your password is case-sensitive')}</b>\n\n"
                f"/cancel - {to_small_caps('cancel the process')}\n\n"
                "👨🏻‍💻 Dev : <a href='https://t.me/anujedits76'>Anuj Kumar</a>",
                parse_mode=ParseMode.HTML
            )
            
        except PhoneCodeInvalidError:
            session_info['otp_attempts'] = session_info.get('otp_attempts', 0) + 1
            left = 3 - session_info['otp_attempts']
            if left > 0:
                await status_msg.edit_text(
                    f"❌ <b>{to_small_caps('invalid otp code! please try again.')}</b>\n\n"
                    f"🔄 {to_small_caps('remaining attempts')}: {left}\n\n"
                    f"📝 {to_small_caps('example')}: 12345\n\n"
                    f"/cancel - {to_small_caps('cancel this process')}\n\n"
                    "👨🏻‍💻 Dev : <a href='https://t.me/anujedits76'>Anuj Kumar</a>",
                    parse_mode=ParseMode.HTML
                )
            else:
                await _disconnect_login(uid)
                await state.clear()
                await status_msg.edit_text(
                    f"❌ {to_small_caps('maximum attempts reached! process cancelled.')}\n\n"
                    f"{to_small_caps('please try again later with /login.')}",
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
                f"❌ <b>{to_small_caps('invalid password! please try again.')}</b>\n\n"
                f"🔄 {to_small_caps('remaining attempts')}: {left}\n\n"
                f"{to_small_caps('if you forgot your password, /cancel and restart with /login')}\n\n"
                "👨🏻‍💻 Dev : <a href='https://t.me/anujedits76'>Anuj Kumar</a>",
                parse_mode=ParseMode.HTML
            )
        else:
            await _disconnect_login(uid)
            await state.clear()
            await status_msg.edit_text(
                f"❌ {to_small_caps('maximum password attempts reached! process cancelled.')}\n\n"
                f"{to_small_caps('please try again later with /login.')}",
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
    if msg.chat.type == ChatType.PRIVATE and await block_if_not_joined(msg):
        return
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
            
            await send_random_pic(uid, caption, reply_markup=kb, parse_mode=None)
            return
        except ValueError:
            pass
    
    # Show approve UI with photo
    kb = await get_approve_kb(uid)
    
    # Check login status
    is_logged_in = str(uid) in user_sessions and user_sessions[str(uid)].get('is_active', False)
    status_text = "🟢 Status: Logged In" if is_logged_in else "🔴 Status: Not Logged In"
    
    await send_random_pic(uid, APPROVE_WELCOME_TEXT + f"\n\n{status_text}", reply_markup=kb, parse_mode=None)

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

def _hs(title: str) -> str:
    return f"<b>{to_small_caps(title)}</b>"

HELP_TEXT = (
    f"📖 <b>{to_small_caps('help & commands')}</b>\n\n"
    f"{_hs('bot commands')}\n"
    "<blockquote>/start — start the bot and open the main menu\n"
    "/cmds — show all commands\n"
    "/autoapprove — toggle auto-approve in a group\n"
    "/approve_all — bulk approve all pending join requests (needs /login)\n"
    "/pending — check, approve or decline pending requests\n"
    "/leave_noti — toggle DM when a member leaves</blockquote>\n\n"
    f"{_hs('userbot commands')}\n"
    "<blockquote>/login — log in your Telegram account for bulk approve\n"
    "/logout — log out your Telegram account\n"
    "/cancel — cancel any active login process</blockquote>\n\n"
    f"{_hs('how to use')}\n"
    "<blockquote>1. Add me as an admin in your group or channel\n"
    "2. Give \"Invite users via link\" admin permission\n"
    "3. Enable join requests on your invite link\n"
    "4. Run /autoapprove in the chat and press Enable\n"
    "5. For /approve_all: first /login in PM, then run it in the group\n"
    "6. OTP format: send digits only, e.g. 12345</blockquote>\n\n"
    "<b>IMPORTANT:</b> the invite link must have \"Approval required\" turned on for join requests to fire."
)

def help_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [make_button("CONTACT", url="https://t.me/anujedits76", style=BTN_PRIMARY)],
        [make_button("« BACK", callback_data="help:back", style=BTN_PRIMARY),
         make_button("✕ CLOSE", callback_data="help:close", style=BTN_DANGER)],
    ])

@dp.message(Command('cmds', 'help'))
async def cmds(msg: types.Message):
    if msg.chat.type == ChatType.PRIVATE and await block_if_not_joined(msg):
        return
    uid = msg.from_user.id
    if not await is_member_of_channel(uid):
        await msg.answer(
            "❌ You must join our channel to use this bot.\n"
            "Please join first and then try again.",
            parse_mode=None,
        )
        return
    
    help_text = HELP_TEXT
    
    await msg.answer(help_text, parse_mode=ParseMode.HTML, reply_markup=help_keyboard(),
                     link_preview_options=types.LinkPreviewOptions(is_disabled=True))

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

async def send_random_pic(chat_id: int, caption: str, reply_markup=None, parse_mode=None):
    """Send a random picture from PICS with caption; fall back to text if Telegram rejects the image."""
    pic = random.choice(PICS)
    try:
        return await bot.send_photo(chat_id=chat_id, photo=pic, caption=caption,
                                    reply_markup=reply_markup, parse_mode=parse_mode)
    except TelegramForbiddenError:
        raise
    except Exception as e:
        logging.warning(f"Random photo failed ({pic}): {e}")
        return await bot.send_message(chat_id=chat_id, text=caption,
                                      reply_markup=reply_markup, parse_mode=parse_mode)

def dm_welcome_markup(chat_id: int):
    rows = []
    for item in group_settings.get(str(chat_id), {}).get('dm_welcome_buttons', []):
        if len(item) >= 2:
            style = item[2] if len(item) > 2 else None
            rows.append([make_button(item[0], url=item[1], style=style)])
    return InlineKeyboardMarkup(inline_keyboard=rows) if rows else None

async def notify_approved(chat_id: int, uid: int):
    try:
        chat_title = await get_chat_name(chat_id)
        try:
            full = (await bot.get_chat(uid)).full_name
        except Exception:
            full = "there"
        custom = group_settings.get(str(chat_id), {}).get('dm_welcome_text')
        if custom:
            first = full.split()[0] if full.split() else full
            text = (custom.replace('{mention}', h(full)).replace('{first}', h(first))
                          .replace('{chat}', h(chat_title)))
            kb, parse = dm_welcome_markup(chat_id), ParseMode.HTML
        else:
            text = (
                f"Hey {full}!!\n"
                f"Your request to join {chat_title} has been approved.\n"
                "Join Request approval Services.\n"
                "Click /start for more info."
            )
            kb, parse = None, None
        # Every approval (single or bulk) comes with a random picture
        try:
            await send_random_pic(uid, text, reply_markup=kb, parse_mode=parse)
        except TelegramForbiddenError:
            raise
        except Exception as e:
            logging.warning(f"Approval photo failed for user {uid}: {e}")
            await bot.send_message(uid, text, reply_markup=kb, parse_mode=parse)
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

@dp.message(Command('status', 'limits'))
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

# ================= PHASE 1: CAPTCHA, FORCE-SUB, GOODBYE =================
CAPTCHA_JOIN_PROTECTION = True      # ask new join requesters to verify before approval
CAPTCHA_TIMEOUT_SECONDS = 90        # request is declined if not verified in time
# Force-sub channels, managed with /fjoin (persisted). Format: {'id': -100..., 'url': 'https://t.me/...'}
FSUB_FN = DATA_DIR / 'force_sub.json'
FORCE_SUB_CHANNELS = load_json(FSUB_FN, [])
GOODBYE_ENABLED = True
GOODBYE_DELETE_AFTER = 600          # seconds; 0 = keep forever

_captcha_tasks = {}                 # (chat_id, user_id) -> timeout task

async def route_join_request(chat_id: int, uid: int):
    """Approve / queue a join request according to the chat's mode."""
    if not chat_setting(chat_id, 'autoapprove'):
        return  # auto-approve is switched off for this chat; requests stay pending for admins
    cid = str(chat_id)
    cfg = limits.get(cid, {})
    mode = cfg.get('mode')
    approved_now = []

    if mode == 'immediate':
        approved_now = await approve_users(chat_id, [uid], cfg)
        cfg['count'] = cfg.get('count', 0) + len(approved_now)

    elif mode == 'limit' and cfg.get('count', 0) < cfg.get('limit', 0):
        approved_now = await approve_users(chat_id, [uid], cfg)
        cfg['count'] = cfg.get('count', 0) + len(approved_now)

    elif mode == 'count':
        pend = cfg.setdefault('pending', [])
        pend.append(uid)
        if len(pend) >= cfg.get('limit', 0):
            approved_now = await approve_users(chat_id, list(pend), cfg)
            pend.clear()

    elif mode == 'time':
        pend = cfg.setdefault('pending', [])
        pend.append(uid)

    save_state()
    for approved_uid in approved_now:
        await notify_approved(chat_id, approved_uid)

async def send_captcha(req: types.ChatJoinRequest):
    title = req.chat.title or "our group"
    text = (
        f"<b>🔐 {to_small_caps('captcha verification')}</b>\n\n"
        f"👋 {h(req.from_user.full_name)}, {to_small_caps('to protect')} "
        f"<b>{h(title)}</b> {to_small_caps('from bots and spam, please verify you are human.')}\n\n"
        f"⏱️ {to_small_caps('time limit')}: {CAPTCHA_TIMEOUT_SECONDS} {to_small_caps('seconds')}\n"
        f"🚫 {to_small_caps('if you do not verify in time, your request will be declined.')}\n\n"
        f"👇 {to_small_caps('tap the button below to verify')}"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        make_button("🤖 I'm not a robot", callback_data=f"captcha_verify:{req.chat.id}:{req.from_user.id}", style=BTN_SUCCESS)
    ]])
    await send_random_pic(req.from_user.id, text, reply_markup=kb, parse_mode=ParseMode.HTML)

async def captcha_timeout(chat_id: int, uid: int):
    try:
        await asyncio.sleep(CAPTCHA_TIMEOUT_SECONDS)
    except asyncio.CancelledError:
        return
    _captcha_tasks.pop((chat_id, uid), None)
    try:
        await bot.decline_chat_join_request(chat_id, uid)
        await bot.send_message(uid, "⏱️ Verification time expired. Send a new join request to try again.", parse_mode=None)
    except Exception as e:
        logging.warning(f"Captcha timeout handling failed for {uid} in {chat_id}: {e}")

@dp.chat_join_request()
async def handle_join_request(req: types.ChatJoinRequest):
    chat_id, uid = req.chat.id, req.from_user.id
    if not CAPTCHA_JOIN_PROTECTION:
        await route_join_request(chat_id, uid)
        return
    try:
        await send_captcha(req)
    except TelegramForbiddenError:
        # User never started the bot, so the captcha cannot reach them.
        logging.warning(f"Captcha not delivered to {uid} (bot not started); using normal approval flow")
        await route_join_request(chat_id, uid)
        return
    except Exception as e:
        logging.warning(f"Captcha send failed for {uid}: {e}; using normal approval flow")
        await route_join_request(chat_id, uid)
        return
    _captcha_tasks[(chat_id, uid)] = asyncio.create_task(captcha_timeout(chat_id, uid))

@dp.callback_query(lambda c: bool(c.data) and c.data.startswith('captcha_verify:'))
async def captcha_verified(cb: CallbackQuery):
    try:
        _, chat_str, uid_str = cb.data.split(':')
        chat_id, uid = int(chat_str), int(uid_str)
    except ValueError:
        await cb.answer("❌ Invalid verification link.", show_alert=True)
        return
    if cb.from_user.id != uid:
        await cb.answer("⛔ This verification link isn't for you!", show_alert=True)
        return
    task = _captcha_tasks.pop((chat_id, uid), None)
    if task is None:
        await cb.answer("ℹ️ Verification already done or expired.", show_alert=True)
        return
    task.cancel()
    await cb.answer("✅ Verification complete! You are approved.", show_alert=True)
    await route_join_request(chat_id, uid)

# ---------- Multi force-sub ----------
async def missing_force_sub(uid: int) -> list:
    missing = []
    for ch in FORCE_SUB_CHANNELS:
        try:
            member = await bot.get_chat_member(ch['id'], uid)
            if member.status in (ChatMemberStatus.LEFT, ChatMemberStatus.KICKED):
                missing.append(ch)
        except Exception as e:
            # Bot cannot check this channel (not admin / wrong id): do not block users for it
            logging.warning(f"Force-sub check skipped for {ch['id']}: {e}")
    return missing

async def block_if_not_joined(msg: types.Message) -> bool:
    """Returns True (and sends the join prompt) if the user still has to join channels."""
    missing = await missing_force_sub(msg.from_user.id)
    if not missing:
        return False
    rows = [[make_button(f"📢 Join channel {i + 1}", url=ch['url'], style=BTN_PRIMARY)] for i, ch in enumerate(missing)]
    rows.append([make_button("✅ I've joined", callback_data="fsub_check", style=BTN_SUCCESS)])
    await msg.answer(
        "❌ <b>Please join our channel(s) first, then tap \"I've joined\".</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows),
        parse_mode=ParseMode.HTML,
    )
    return True

@dp.callback_query(lambda c: c.data == 'fsub_check')
async def fsub_check(cb: CallbackQuery):
    uid = cb.from_user.id
    if await missing_force_sub(uid):
        await cb.answer("❌ You have not joined all channels yet.", show_alert=True)
        return
    await cb.answer("✅ Thanks for joining!")
    if uid not in accepted_users:
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            make_button('✅ Accept & Continue', callback_data='accept_privacy', style=BTN_SUCCESS)
        ]])
        await bot.send_message(uid, PRIVACY_POLICY_TEXT, reply_markup=kb, parse_mode=None)
    else:
        send_welcome_to_user(uid)

# ---------- Goodbye message ----------
async def _delete_later(message, delay: int):
    await asyncio.sleep(delay)
    try:
        await message.delete()
    except Exception:
        pass

@dp.message(F.left_chat_member)
async def goodbye_member(msg: types.Message):
    if not GOODBYE_ENABLED or msg.chat.type not in (ChatType.GROUP, ChatType.SUPERGROUP):
        return
    if not chat_setting(msg.chat.id, 'goodbye'):
        return
    user = msg.left_chat_member
    if user is None or user.is_bot:
        return
    asyncio.create_task(notify_leave_to_admins(msg.chat, user))
    entries = leaves_db.setdefault(str(msg.chat.id), [])
    entries.append({'uid': user.id, 'name': user.full_name, 'time': datetime.now(timezone.utc).isoformat()})
    del entries[:-200]
    _save(LEAVES_FN, leaves_db)
    title = h(msg.chat.title or "this group")
    custom = group_settings.get(str(msg.chat.id), {}).get('goodbye_text')
    if custom:
        text = render_custom_text(custom, user, msg.chat)
    else:
        text = (
            f"<b>{to_small_caps('we are missing you')}, {h(user.full_name)} 👋</b>\n\n"
            f"{to_small_caps('hope to see you again in')} <b>{title}</b>."
        )
    try:
        sent = await send_random_pic(msg.chat.id, text, parse_mode=ParseMode.HTML)
    except Exception as e:
        logging.warning(f"Goodbye message failed in {msg.chat.id}: {e}")
        return
    if GOODBYE_DELETE_AFTER > 0:
        task = asyncio.create_task(_delete_later(sent, GOODBYE_DELETE_AFTER))
        _background_tasks.add(task)
        task.add_done_callback(_background_tasks.discard)


# ================= PHASE 2 & 3: GROUP MANAGEMENT (JSON storage) =================
FLOOD_LIMIT = 5                 # messages
FLOOD_WINDOW = 10               # seconds
FLOOD_MUTE_SECONDS = 300
WARN_LIMIT = 3                  # warnings before automatic ban
MUTE_DEFAULT_SECONDS = 3600

BLACKLIST_FN = DATA_DIR / 'blacklist.json'
NOTES_FN = DATA_DIR / 'notes.json'
FILTERS_FN = DATA_DIR / 'filters.json'
LOCKS_FN = DATA_DIR / 'locks.json'
WARNS_FN = DATA_DIR / 'warns.json'
LOCK_TYPES = ('links', 'stickers', 'photos', 'videos', 'forwards')

blacklist = load_json(BLACKLIST_FN, {})   # chat -> [words]
notes = load_json(NOTES_FN, {})           # chat -> {name: text}
filters_db = load_json(FILTERS_FN, {})    # chat -> {keyword: reply}
locks = load_json(LOCKS_FN, {})           # chat -> [types]
warns = load_json(WARNS_FN, {})           # chat -> {uid: count}
_flood_hits = {}                          # (chat, uid) -> [timestamps]
_admin_cache = {}                         # (chat, uid) -> (is_admin, expires_at)

GROUP_TYPES = (ChatType.GROUP, ChatType.SUPERGROUP)

async def is_admin_cached(chat_id: int, uid: int) -> bool:
    key = (chat_id, uid)
    hit = _admin_cache.get(key)
    now = time.monotonic()
    if hit and hit[1] > now:
        return hit[0]
    value = await is_chat_admin(chat_id, uid)
    _admin_cache[key] = (value, now + 300)
    return value

BOT_ADMINS_FN = DATA_DIR / 'bot_admins.json'
LEAVES_FN = DATA_DIR / 'leaves.json'
bot_admins = set(load_json(BOT_ADMINS_FN, []))   # extra bot admins (owner always allowed)
leaves_db = load_json(LEAVES_FN, {})              # chat -> [{uid, name, time}]

SETTINGS_FN = DATA_DIR / 'group_settings.json'
group_settings = load_json(SETTINGS_FN, {})       # chat -> {key: bool}
GROUP_SETTING_KEYS = {
    'welcome': 'Welcome message',
    'goodbye': 'Goodbye message',
    'antiflood': 'Anti-flood',
}

def chat_setting(chat_id: int, key: str) -> bool:
    return bool(group_settings.get(str(chat_id), {}).get(key, True))

LAST_SEEN_FN = DATA_DIR / 'last_seen.json'
user_last_seen = load_json(LAST_SEEN_FN, {})      # uid(str) -> unix time

def touch_user(uid: int):
    user_last_seen[str(uid)] = time.time()
    save_json(LAST_SEEN_FN, user_last_seen)

def active_users_within(days: int) -> int:
    cutoff = time.time() - days * 86400
    return sum(1 for t in user_last_seen.values() if t >= cutoff)

def is_bot_admin(uid: int) -> bool:
    return uid == OWNER_ID or uid in bot_admins

def _save(path, data):
    save_json(path, data)

def _until(seconds: int):
    return datetime.now(timezone.utc) + timedelta(seconds=seconds)

async def _target_user(msg: types.Message):
    """Reply target or numeric user id from the command arguments."""
    if msg.reply_to_message and msg.reply_to_message.from_user:
        return msg.reply_to_message.from_user
    parts = (msg.text or '').split()
    if len(parts) >= 2:
        arg = parts[1]
        if arg.lstrip('-').isdigit():
            return types.User(id=int(arg), is_bot=False, first_name=arg)
        if arg.startswith('@'):
            try:
                chat = await bot.get_chat(arg)
                return types.User(id=chat.id, is_bot=False, first_name=getattr(chat, 'full_name', None) or arg)
            except Exception:
                return None
    return None

async def _require_admin(msg: types.Message) -> bool:
    if not await is_admin_cached(msg.chat.id, msg.from_user.id):
        await msg.reply("❌ Only group admins can use this command.")
        return False
    return True

# --- Moderation -------------------------------------------------------------
@dp.message(Command('ban'), F.chat.type.in_(GROUP_TYPES))
async def cmd_ban(msg: types.Message):
    if not await _require_admin(msg):
        return
    target = await _target_user(msg)
    if not target:
        return await msg.reply("Usage: reply to a user with /ban, or /ban &lt;user_id&gt;")
    try:
        await bot.ban_chat_member(msg.chat.id, target.id)
        await msg.reply(f"🚫 {h(target.full_name)} banned.", parse_mode=ParseMode.HTML)
    except Exception as e:
        await msg.reply(f"❌ Ban failed: {h(str(e))}", parse_mode=ParseMode.HTML)

@dp.message(Command('unban'), F.chat.type.in_(GROUP_TYPES))
async def cmd_unban(msg: types.Message):
    if not await _require_admin(msg):
        return
    target = await _target_user(msg)
    if not target:
        return await msg.reply("Usage: reply to a user with /unban, or /unban &lt;user_id&gt;")
    try:
        await bot.unban_chat_member(msg.chat.id, target.id, only_if_banned=True)
        await msg.reply(f"✅ {h(target.full_name)} unbanned.", parse_mode=ParseMode.HTML)
    except Exception as e:
        await msg.reply(f"❌ Unban failed: {h(str(e))}", parse_mode=ParseMode.HTML)

@dp.message(Command('kick'), F.chat.type.in_(GROUP_TYPES))
async def cmd_kick(msg: types.Message):
    if not await _require_admin(msg):
        return
    target = await _target_user(msg)
    if not target:
        return await msg.reply("Usage: reply to a user with /kick, or /kick &lt;user_id&gt;")
    try:
        await bot.ban_chat_member(msg.chat.id, target.id)
        await bot.unban_chat_member(msg.chat.id, target.id, only_if_banned=True)
        await msg.reply(f"👢 {h(target.full_name)} kicked.", parse_mode=ParseMode.HTML)
    except Exception as e:
        await msg.reply(f"❌ Kick failed: {h(str(e))}", parse_mode=ParseMode.HTML)

@dp.message(Command('mute'), F.chat.type.in_(GROUP_TYPES))
async def cmd_mute(msg: types.Message):
    if not await _require_admin(msg):
        return
    target = await _target_user(msg)
    if not target:
        return await msg.reply("Usage: reply to a user with /mute, or /mute &lt;user_id&gt;")
    try:
        await bot.restrict_chat_member(msg.chat.id, target.id,
                                       permissions=ChatPermissions(can_send_messages=False),
                                       until_date=_until(MUTE_DEFAULT_SECONDS))
        await msg.reply(f"🔇 {h(target.full_name)} muted for 1 hour.", parse_mode=ParseMode.HTML)
    except Exception as e:
        await msg.reply(f"❌ Mute failed: {h(str(e))}", parse_mode=ParseMode.HTML)

@dp.message(Command('unmute'), F.chat.type.in_(GROUP_TYPES))
async def cmd_unmute(msg: types.Message):
    if not await _require_admin(msg):
        return
    target = await _target_user(msg)
    if not target:
        return await msg.reply("Usage: reply to a user with /unmute, or /unmute &lt;user_id&gt;")
    try:
        await bot.restrict_chat_member(msg.chat.id, target.id, permissions=ChatPermissions(
            can_send_messages=True, can_send_audios=True, can_send_documents=True,
            can_send_photos=True, can_send_videos=True, can_send_video_notes=True,
            can_send_voice_notes=True, can_send_polls=True, can_send_other_messages=True,
            can_add_web_page_previews=True))
        await msg.reply(f"🔊 {h(target.full_name)} unmuted.", parse_mode=ParseMode.HTML)
    except Exception as e:
        await msg.reply(f"❌ Unmute failed: {h(str(e))}", parse_mode=ParseMode.HTML)

@dp.message(Command('warn'), F.chat.type.in_(GROUP_TYPES))
async def cmd_warn(msg: types.Message):
    if not await _require_admin(msg):
        return
    target = await _target_user(msg)
    if not target:
        return await msg.reply("Usage: reply to a user with /warn")
    chat_w = warns.setdefault(str(msg.chat.id), {})
    count = chat_w.get(str(target.id), 0) + 1
    if count >= WARN_LIMIT:
        chat_w.pop(str(target.id), None)
        _save(WARNS_FN, warns)
        try:
            await bot.ban_chat_member(msg.chat.id, target.id)
            return await msg.reply(f"🚫 {h(target.full_name)} reached {WARN_LIMIT} warnings and was banned.", parse_mode=ParseMode.HTML)
        except Exception as e:
            return await msg.reply(f"❌ Auto-ban failed: {h(str(e))}", parse_mode=ParseMode.HTML)
    chat_w[str(target.id)] = count
    _save(WARNS_FN, warns)
    await msg.reply(f"⚠️ {h(target.full_name)} warned ({count}/{WARN_LIMIT}).", parse_mode=ParseMode.HTML)

@dp.message(Command('warns', 'warnings'), F.chat.type.in_(GROUP_TYPES))
async def cmd_warns(msg: types.Message):
    target = (await _target_user(msg)) or msg.from_user
    count = warns.get(str(msg.chat.id), {}).get(str(target.id), 0)
    await msg.reply(f"⚠️ {h(target.full_name)} has {count}/{WARN_LIMIT} warnings.", parse_mode=ParseMode.HTML)

@dp.message(Command('resetwarn'), F.chat.type.in_(GROUP_TYPES))
async def cmd_resetwarn(msg: types.Message):
    if not await _require_admin(msg):
        return
    target = await _target_user(msg)
    if not target:
        return await msg.reply("Usage: reply to a user with /resetwarn")
    warns.get(str(msg.chat.id), {}).pop(str(target.id), None)
    _save(WARNS_FN, warns)
    await msg.reply(f"✅ Warnings reset for {h(target.full_name)}.", parse_mode=ParseMode.HTML)

@dp.message(Command('report'), F.chat.type.in_(GROUP_TYPES))
async def cmd_report(msg: types.Message):
    if not msg.reply_to_message or not msg.reply_to_message.from_user:
        return await msg.reply("Reply to the message you want to report with /report.")
    reported = msg.reply_to_message
    text = (
        f"🚨 <b>Report</b> in {h(msg.chat.title or '')}\n"
        f"👤 Reported: {h(reported.from_user.full_name)} (<code>{reported.from_user.id}</code>)\n"
        f"🙋 By: {h(msg.from_user.full_name)}\n"
        f"🔗 Message: {reported.message_id}"
    )
    try:
        admins = await bot.get_chat_administrators(msg.chat.id)
    except Exception:
        admins = []
    sent = 0
    for adm in admins:
        if adm.user.is_bot:
            continue
        try:
            await bot.send_message(adm.user.id, text, parse_mode=ParseMode.HTML)
            sent += 1
        except Exception:
            pass
    await msg.reply(f"✅ Report sent to {sent} admin(s).")

# --- Locks -------------------------------------------------------------------
@dp.message(Command('lock', 'unlock'), F.chat.type.in_(GROUP_TYPES))
async def cmd_lock(msg: types.Message):
    if not await _require_admin(msg):
        return
    parts = (msg.text or '').split()
    cmd = parts[0].lower().lstrip('/').split('@')[0]
    if len(parts) < 2 or parts[1].lower() not in LOCK_TYPES:
        return await msg.reply("Usage: /lock or /unlock with one of: " + ', '.join(LOCK_TYPES))
    kind = parts[1].lower()
    current = set(locks.get(str(msg.chat.id), []))
    if cmd == 'lock':
        current.add(kind)
    else:
        current.discard(kind)
    locks[str(msg.chat.id)] = sorted(current)
    _save(LOCKS_FN, locks)
    await msg.reply(f"🔒 {kind} {'locked' if cmd == 'lock' else 'unlocked'}.")

# --- Blacklist ---------------------------------------------------------------
@dp.message(Command('blacklist', 'unblacklist'), F.chat.type.in_(GROUP_TYPES))
async def cmd_blacklist(msg: types.Message):
    if not await _require_admin(msg):
        return
    parts = (msg.text or '').split(maxsplit=1)
    cmd = parts[0].lower().lstrip('/').split('@')[0]
    if len(parts) < 2:
        return await msg.reply("Usage: /blacklist word or phrase")
    word = parts[1].strip().lower()
    words = blacklist.setdefault(str(msg.chat.id), [])
    if cmd == 'blacklist' and word not in words:
        words.append(word)
    elif cmd == 'unblacklist' and word in words:
        words.remove(word)
    _save(BLACKLIST_FN, blacklist)
    await msg.reply("✅ Blacklist updated.")

@dp.message(Command('blacklists'), F.chat.type.in_(GROUP_TYPES))
async def cmd_blacklists(msg: types.Message):
    words = blacklist.get(str(msg.chat.id), [])
    await msg.reply("🚫 Blacklist:\n• " + "\n• ".join(sorted(words)) if words else "Blacklist is empty.")

# --- Notes -------------------------------------------------------------------
@dp.message(Command('save'), F.chat.type.in_(GROUP_TYPES))
async def cmd_save(msg: types.Message):
    if not await _require_admin(msg):
        return
    parts = (msg.text or '').split(maxsplit=2)
    if len(parts) < 3:
        return await msg.reply("Usage: /save &lt;name&gt; &lt;text&gt;")
    notes.setdefault(str(msg.chat.id), {})[parts[1].lower()] = parts[2]
    _save(NOTES_FN, notes)
    await msg.reply(f"✅ Note '{parts[1].lower()}' saved. Get it with /get {parts[1].lower()} or #{parts[1].lower()}")

@dp.message(Command('get'), F.chat.type.in_(GROUP_TYPES))
async def cmd_get(msg: types.Message):
    parts = (msg.text or '').split(maxsplit=1)
    if len(parts) < 2:
        return await msg.reply("Usage: /get &lt;name&gt;")
    text = notes.get(str(msg.chat.id), {}).get(parts[1].strip().lower())
    await msg.reply(text or "No such note.")

@dp.message(Command('notes'), F.chat.type.in_(GROUP_TYPES))
async def cmd_notes(msg: types.Message):
    names = sorted(notes.get(str(msg.chat.id), {}).keys())
    await msg.reply("📝 Notes:\n• " + "\n• ".join(names) if names else "No notes saved.")

# --- Filters (keyword auto-reply) -------------------------------------------
@dp.message(Command('filter', 'stopfilter', 'stop', 'filters'), F.chat.type.in_(GROUP_TYPES))
async def cmd_filter(msg: types.Message):
    parts = (msg.text or '').split(maxsplit=2)
    cmd = parts[0].lower().lstrip('/').split('@')[0]
    chat_f = filters_db.setdefault(str(msg.chat.id), {})
    if cmd == 'filters':
        return await msg.reply("🔎 Filters:\n• " + "\n• ".join(sorted(chat_f)) if chat_f else "No filters set.")
    if not await _require_admin(msg):
        return
    if cmd == 'filter':
        if len(parts) < 3:
            return await msg.reply("Usage: /filter &lt;keyword&gt; &lt;reply text&gt;")
        chat_f[parts[1].lower()] = parts[2]
        _save(FILTERS_FN, filters_db)
        return await msg.reply(f"✅ Filter '{parts[1].lower()}' added.")
    if len(parts) < 2:
        return await msg.reply("Usage: /stopfilter &lt;keyword&gt;")
    chat_f.pop(parts[1].lower(), None)
    _save(FILTERS_FN, filters_db)
    await msg.reply("✅ Filter removed.")

# --- Group guard: anti-flood, blacklist, locks, notes (#name), filters -------
def _is_normal_group_message(m: types.Message) -> bool:
    return m.left_chat_member is None and not (m.new_chat_members) and not (m.text or '').startswith('/')

@dp.message(F.chat.type.in_(GROUP_TYPES), _is_normal_group_message)
async def group_guard(msg: types.Message):
    if not msg.from_user or msg.from_user.is_bot:
        return
    if await is_admin_cached(msg.chat.id, msg.from_user.id):
        return
    chat_key = str(msg.chat.id)
    text = msg.text or msg.caption or ''

    # Blacklist
    if text and any(re.search(r'(?<!\w)' + re.escape(w) + r'(?!\w)', text, re.I)
                    for w in blacklist.get(chat_key, [])):
        try:
            await msg.delete()
        except Exception:
            pass
        return

    # Locks
    active = set(locks.get(chat_key, []))
    blocked = (
        ('links' in active and re.search(r'https?://|t\.me/|www\.', text, re.I)) or
        ('stickers' in active and msg.sticker) or
        ('photos' in active and msg.photo) or
        ('videos' in active and msg.video) or
        ('forwards' in active and msg.forward_date)
    )
    if blocked:
        try:
            await msg.delete()
        except Exception:
            pass
        return

    # Anti-flood
    key = (msg.chat.id, msg.from_user.id)
    now = time.monotonic()
    q = [t for t in _flood_hits.get(key, []) if now - t <= FLOOD_WINDOW]
    q.append(now)
    _flood_hits[key] = q
    if chat_setting(msg.chat.id, 'antiflood') and len(q) >= FLOOD_LIMIT:
        _flood_hits[key] = []
        try:
            await bot.restrict_chat_member(msg.chat.id, msg.from_user.id,
                                           permissions=ChatPermissions(can_send_messages=False),
                                           until_date=_until(FLOOD_MUTE_SECONDS))
            await msg.answer(f"🔇 {h(msg.from_user.full_name)} muted for flooding.", parse_mode=ParseMode.HTML)
        except Exception as e:
            logging.warning(f"Anti-flood mute failed: {e}")
        return

    # Notes via #name
    if text.startswith('#') and len(text) > 1:
        note = notes.get(chat_key, {}).get(text[1:].split()[0].lower())
        if note:
            return await msg.reply(note)

    # Keyword filters
    for kw, reply_text in filters_db.get(chat_key, {}).items():
        if re.search(r'(?<!\w)' + re.escape(kw) + r'(?!\w)', text, re.I):
            return await msg.reply(reply_text)

# ================= PHASE 2: FEEDBACK, STATS, UNJOINED =================
@dp.message(Command('feedback'), F.chat.type == ChatType.PRIVATE)
async def cmd_feedback(msg: types.Message):
    body = (msg.text or '').split(maxsplit=1)
    if len(body) < 2:
        return await msg.answer("Usage: /feedback your message")
    try:
        await bot.send_message(OWNER_ID,
            f"💬 <b>Feedback</b>\nFrom: {h(msg.from_user.full_name)} (<code>{msg.from_user.id}</code>)\n\n{h(body[1])}",
            parse_mode=ParseMode.HTML)
        await msg.answer("✅ Thanks! Your feedback was sent.")
    except Exception as e:
        logging.warning(f"Feedback delivery failed: {e}")
        await msg.answer("❌ Could not send feedback right now.")

@dp.message(Command('stats'), F.chat.type == ChatType.PRIVATE)
async def cmd_stats(msg: types.Message):
    if not is_bot_admin(msg.from_user.id):
        return
    active = sum(1 for v in user_sessions.values() if v.get('is_active'))
    await msg.answer(
        "📊 <b>Bot stats</b>\n\n"
        f"👥 Privacy-accepted users: {len(accepted_users)}\n"
        f"📢 Registered groups/channels: {len(groups)}\n"
        f"🔑 Logged-in accounts: {active}\n"
        f"⚙️ Chats with a mode set: {len(limits)}\n"
        f"📅 Monthly active users: {active_users_within(30)}\n"
        f"🤖 Captchas pending: {len(_captcha_tasks)}",
        parse_mode=ParseMode.HTML)

@dp.message(Command('unjoined'), F.chat.type == ChatType.PRIVATE)
async def cmd_unjoined(msg: types.Message):
    if not is_bot_admin(msg.from_user.id):
        return
    if not FORCE_SUB_CHANNELS:
        return await msg.answer("No force-sub channels configured.")
    unjoined = []
    for uid in list(accepted_users):
        if await missing_force_sub(uid):
            unjoined.append(uid)
    preview = "\n".join(f"• <code>{u}</code>" for u in unjoined[:50])
    await msg.answer(f"🔍 Users who have not joined all force-sub channels: {len(unjoined)}\n{preview}",
                     parse_mode=ParseMode.HTML)


# ================= ALL REMAINING FEATURES =================
GROUP_WELCOME_ENABLED = True

@dp.message(F.new_chat_members, F.chat.type.in_(GROUP_TYPES))
async def group_welcome(msg: types.Message):
    if not GROUP_WELCOME_ENABLED or not chat_setting(msg.chat.id, 'welcome'):
        return
    for user in msg.new_chat_members:
        if user.is_bot:
            continue
        custom = group_settings.get(str(msg.chat.id), {}).get('welcome_text')
        if custom:
            text = render_custom_text(custom, user, msg.chat)
        else:
            text = (
                f"<b>{to_small_caps('welcome')}, {h(user.full_name)} 👋</b>\n\n"
                f"{to_small_caps('glad to have you in')} <b>{h(msg.chat.title or '')}</b>.\n\n"
                f"💬 {h(random.choice(QUOTES))}"
            )
        try:
            sent = await send_random_pic(msg.chat.id, text, parse_mode=ParseMode.HTML)
        except Exception as e:
            logging.warning(f"Group welcome failed in {msg.chat.id}: {e}")
            continue
        task = asyncio.create_task(_delete_later(sent, GOODBYE_DELETE_AFTER or 600))
        _background_tasks.add(task)
        task.add_done_callback(_background_tasks.discard)

@dp.message(Command('addadmin', 'rmadmin'), F.chat.type == ChatType.PRIVATE)
async def cmd_admin_mgmt(msg: types.Message):
    if msg.from_user.id != OWNER_ID:
        return await msg.answer("❌ Only the owner can manage bot admins.")
    target = await _target_user(msg)
    if not target:
        return await msg.answer("Usage: /addadmin &lt;user_id or @username&gt;  or reply to a user")
    cmd = msg.text.split()[0].lower().lstrip('/').split('@')[0]
    if cmd == 'addadmin':
        bot_admins.add(target.id)
    else:
        bot_admins.discard(target.id)
    save_json(BOT_ADMINS_FN, list(bot_admins))
    await msg.answer(f"✅ {'Added' if cmd == 'addadmin' else 'Removed'} admin: <code>{target.id}</code>", parse_mode=ParseMode.HTML)

@dp.message(Command('admins'), F.chat.type == ChatType.PRIVATE)
async def cmd_admins(msg: types.Message):
    if not is_bot_admin(msg.from_user.id):
        return
    ids = sorted(bot_admins)
    await msg.answer("👑 Bot admins:\n• <code>%d</code> (owner)\n" % OWNER_ID + "\n".join(f"• <code>{i}</code>" for i in ids), parse_mode=ParseMode.HTML)

@dp.message(Command('users'), F.chat.type == ChatType.PRIVATE)
async def cmd_users(msg: types.Message):
    if not is_bot_admin(msg.from_user.id):
        return
    users = sorted(accepted_users)
    body = "\n".join(f"• <code>{u}</code>" for u in users[:100])
    more = f"\n…and {len(users) - 100} more" if len(users) > 100 else ""
    await msg.answer(f"👥 Users: {len(users)}\n{body}{more}", parse_mode=ParseMode.HTML)

@dp.message(Command('broadcast'), F.chat.type == ChatType.PRIVATE)
async def cmd_broadcast(msg: types.Message):
    if not is_bot_admin(msg.from_user.id):
        return
    src = msg.reply_to_message
    body = None
    if not src:
        parts = (msg.text or '').split(maxsplit=1)
        if len(parts) < 2:
            return await msg.answer("Usage: reply to a message with /broadcast, or /broadcast &lt;text&gt;")
        body = parts[1]
    status = await msg.answer("📡 Broadcasting...")
    ok = fail = 0
    for uid in list(accepted_users):
        try:
            if src:
                await bot.copy_message(uid, from_chat_id=msg.chat.id, message_id=src.message_id)
            else:
                await bot.send_message(uid, body, parse_mode=None)
            ok += 1
        except Exception:
            fail += 1
        await asyncio.sleep(0.05)
    await status.edit_text(f"✅ Broadcast done. Sent: {ok}, failed: {fail}")

@dp.message(Command('leaves'), F.chat.type.in_(GROUP_TYPES))
async def cmd_leaves(msg: types.Message):
    if not await _require_admin(msg):
        return
    entries = leaves_db.get(str(msg.chat.id), [])[-20:]
    if not entries:
        return await msg.reply("No leave events recorded.")
    lines = [f"• {h(e['name'])} (<code>{e['uid']}</code>) — {e['time'][:16].replace('T', ' ')} UTC" for e in reversed(entries)]
    await msg.reply("🚪 Recent leaves:\n" + "\n".join(lines), parse_mode=ParseMode.HTML)

def _group_panel_markup(cid: int) -> InlineKeyboardMarkup:
    rows = []
    for key, label in GROUP_SETTING_KEYS.items():
        state = "✅ On" if chat_setting(cid, key) else "❌ Off"
        rows.append([make_button(f"{label}: {state}", callback_data=f"grp:toggle:{key}:{cid}",
                                 style=BTN_SUCCESS if chat_setting(cid, key) else BTN_DANGER)])
    rows.append([make_button("⬅️ Back to groups", callback_data="grp:list", style=BTN_PRIMARY)])
    return InlineKeyboardMarkup(inline_keyboard=rows)

async def _admin_groups(uid: int) -> list:
    out = []
    for cid, title in list(groups.items()):
        try:
            if await is_chat_admin(int(cid), uid):
                out.append((int(cid), str(title)))
        except Exception:
            continue
    return out

@dp.message(Command('groups'), F.chat.type == ChatType.PRIVATE)
async def cmd_groups(msg: types.Message):
    """Private group control: pick a group where you are admin and toggle its features."""
    gs = await _admin_groups(msg.from_user.id)
    if not gs:
        return await msg.answer("You are not an admin of any registered group. Add the bot to a group first.")
    rows = [[make_button(title[:40], callback_data=f"grp:open:{cid}", style=BTN_PRIMARY)] for cid, title in gs]
    await msg.answer("🛠 <b>Select a group to manage:</b>", reply_markup=InlineKeyboardMarkup(inline_keyboard=rows), parse_mode=ParseMode.HTML)

@dp.callback_query(lambda c: bool(c.data) and c.data.startswith('grp:'))
async def group_panel_callback(cb: CallbackQuery):
    parts = cb.data.split(':')
    action = parts[1]
    if action == 'list':
        gs = await _admin_groups(cb.from_user.id)
        rows = [[make_button(title[:40], callback_data=f"grp:open:{cid}", style=BTN_PRIMARY)] for cid, title in gs]
        await cb.message.edit_text("🛠 <b>Select a group to manage:</b>", reply_markup=InlineKeyboardMarkup(inline_keyboard=rows), parse_mode=ParseMode.HTML)
        return await cb.answer()
    try:
        cid = int(parts[-1])
    except ValueError:
        return await cb.answer("❌ Invalid group.", show_alert=True)
    if not await is_chat_admin(cid, cb.from_user.id):
        return await cb.answer("⛔ You are not an admin of that group.", show_alert=True)
    if action == 'toggle' and len(parts) == 4:
        key = parts[2]
        if key in GROUP_SETTING_KEYS:
            current = group_settings.setdefault(str(cid), {})
            current[key] = not chat_setting(cid, key)
            save_json(SETTINGS_FN, group_settings)
    title = groups.get(str(cid), str(cid))
    await cb.message.edit_text(f"⚙️ <b>{h(str(title))}</b>\nTap to toggle features.",
                               reply_markup=_group_panel_markup(cid), parse_mode=ParseMode.HTML)
    await cb.answer()


# ================= REMAINING SPIDEY COMMANDS =================
def render_custom_text(template: str, user, chat) -> str:
    return (template.replace('{mention}', h(user.full_name))
                    .replace('{chat}', h(chat.title or 'this group')))

def parse_duration(token: str):
    """'30m' / '2h' / '1d' / '45s' -> seconds, else None."""
    m = re.fullmatch(r'(\d+)([smhd])', (token or '').lower())
    if not m:
        return None
    return int(m.group(1)) * {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}[m.group(2)]

@dp.message(Command('welcome', 'goodbye', 'antiflood'), F.chat.type.in_(GROUP_TYPES))
async def cmd_toggle_setting(msg: types.Message):
    if not await _require_admin(msg):
        return
    parts = (msg.text or '').split()
    key = parts[0].lower().lstrip('/').split('@')[0]
    if len(parts) < 2 or parts[1].lower() not in ('on', 'off'):
        return await msg.reply(f"Usage: /{key} on|off")
    group_settings.setdefault(str(msg.chat.id), {})[key] = parts[1].lower() == 'on'
    save_json(SETTINGS_FN, group_settings)
    await msg.reply(f"✅ {key} is now {parts[1].lower()}.")

@dp.message(Command('setwelcome', 'setgoodbye'), F.chat.type.in_(GROUP_TYPES))
async def cmd_set_custom_text(msg: types.Message):
    if not await _require_admin(msg):
        return
    parts = (msg.text or '').split(maxsplit=1)
    key = 'welcome_text' if parts[0].lower().lstrip('/').split('@')[0] == 'setwelcome' else 'goodbye_text'
    if len(parts) < 2:
        return await msg.reply("Usage: /setwelcome &lt;text&gt;  (placeholders: {mention}, {chat})")
    group_settings.setdefault(str(msg.chat.id), {})[key] = parts[1]
    save_json(SETTINGS_FN, group_settings)
    await msg.reply("✅ Custom text saved.")

@dp.message(Command('locks'), F.chat.type.in_(GROUP_TYPES))
async def cmd_locks(msg: types.Message):
    active = locks.get(str(msg.chat.id), [])
    await msg.reply("🔒 Active locks: " + (", ".join(active) if active else "none"))

@dp.message(Command('clear'), F.chat.type.in_(GROUP_TYPES))
async def cmd_clear_note(msg: types.Message):
    if not await _require_admin(msg):
        return
    parts = (msg.text or '').split()
    if len(parts) < 2:
        return await msg.reply("Usage: /clear &lt;note name&gt;")
    removed = notes.get(str(msg.chat.id), {}).pop(parts[1].lower(), None)
    _save(NOTES_FN, notes)
    await msg.reply("✅ Note deleted." if removed is not None else "Note not found.")

@dp.message(Command('unwarn'), F.chat.type.in_(GROUP_TYPES))
async def cmd_unwarn(msg: types.Message):
    if not await _require_admin(msg):
        return
    target = await _target_user(msg)
    if not target:
        return await msg.reply("Usage: reply to a user with /unwarn")
    chat_w = warns.setdefault(str(msg.chat.id), {})
    count = max(0, chat_w.get(str(target.id), 0) - 1)
    chat_w[str(target.id)] = count
    _save(WARNS_FN, warns)
    await msg.reply(f"✅ Removed one warning from {h(target.full_name)} ({count}/{WARN_LIMIT}).", parse_mode=ParseMode.HTML)

@dp.message(Command('tban', 'tmute'), F.chat.type.in_(GROUP_TYPES))
async def cmd_temp_restrict(msg: types.Message):
    if not await _require_admin(msg):
        return
    parts = (msg.text or '').split()
    cmd = parts[0].lower().lstrip('/').split('@')[0]
    target = await _target_user(msg)
    # duration is the token after the user argument (or the first token when replying)
    dur_token = parts[-1] if msg.reply_to_message else (parts[2] if len(parts) > 2 else None)
    seconds = parse_duration(dur_token)
    if not target or not seconds:
        return await msg.reply(f"Usage: reply with /{cmd} 30m|2h|1d  or  /{cmd} &lt;user_id&gt; 30m")
    try:
        until = _until(seconds)
        if cmd == 'tban':
            await bot.ban_chat_member(msg.chat.id, target.id, until_date=until)
            await msg.reply(f"🚫 {h(target.full_name)} banned for {dur_token}.", parse_mode=ParseMode.HTML)
        else:
            await bot.restrict_chat_member(msg.chat.id, target.id,
                                           permissions=ChatPermissions(can_send_messages=False), until_date=until)
            await msg.reply(f"🔇 {h(target.full_name)} muted for {dur_token}.", parse_mode=ParseMode.HTML)
    except Exception as e:
        await msg.reply(f"❌ Failed: {h(str(e))}", parse_mode=ParseMode.HTML)

@dp.message(Command('del'), F.chat.type.in_(GROUP_TYPES))
async def cmd_del(msg: types.Message):
    if not await _require_admin(msg):
        return
    if not msg.reply_to_message:
        return await msg.reply("Reply to the message you want to delete with /del.")
    try:
        await bot.delete_messages(msg.chat.id, [msg.reply_to_message.message_id, msg.message_id])
    except Exception as e:
        await msg.reply(f"❌ Delete failed: {h(str(e))}", parse_mode=ParseMode.HTML)

@dp.message(Command('purge'), F.chat.type.in_(GROUP_TYPES))
async def cmd_purge(msg: types.Message):
    if not await _require_admin(msg):
        return
    if not msg.reply_to_message:
        return await msg.reply("Reply to the first message you want to purge with /purge.")
    start, end = msg.reply_to_message.message_id, msg.message_id
    ids = list(range(start, end + 1))
    deleted = 0
    for i in range(0, len(ids), 100):
        chunk = ids[i:i + 100]
        try:
            await bot.delete_messages(msg.chat.id, chunk)
            deleted += len(chunk)
        except Exception as e:
            logging.warning(f"Purge chunk failed: {e}")
    await bot.send_message(msg.chat.id, f"🧹 Purged {deleted} message(s).")

@dp.message(Command('info'))
async def cmd_info(msg: types.Message):
    target = (msg.reply_to_message.from_user if msg.reply_to_message and msg.reply_to_message.from_user
              else await _target_user(msg) or msg.from_user)
    await msg.answer(
        f"👤 <b>User info</b>\nName: {h(target.full_name)}\nID: <code>{target.id}</code>\n"
        f"Username: @{h(target.username) if target.username else 'none'}",
        parse_mode=ParseMode.HTML)

@dp.message(Command('leave'), F.chat.type.in_(GROUP_TYPES))
async def cmd_leave(msg: types.Message):
    if not is_bot_admin(msg.from_user.id):
        return
    await msg.answer("👋 Leaving this group.")
    try:
        await bot.leave_chat(msg.chat.id)
    except Exception as e:
        logging.warning(f"Leave failed: {e}")

@dp.message(Command('send'), F.chat.type == ChatType.PRIVATE)
async def cmd_send(msg: types.Message):
    if not is_bot_admin(msg.from_user.id):
        return
    src = msg.reply_to_message
    parts = (msg.text or '').split()
    if not src or len(parts) < 2:
        return await msg.answer("Reply to a message with /send &lt;user_id&gt; [user_id ...]")
    ok = fail = 0
    for tok in parts[1:]:
        if not tok.lstrip('-').isdigit():
            fail += 1
            continue
        try:
            await bot.copy_message(int(tok), from_chat_id=msg.chat.id, message_id=src.message_id)
            ok += 1
        except Exception:
            fail += 1
    await msg.answer(f"✅ Sent: {ok}, failed: {fail}")


# ================= PING, AUTO-APPROVE TOGGLE, APPROVE_ALL, LEAVE NOTI, PBROADCAST, RESTART =================
BOT_START = time.time()
LEAVE_NOTI_FN = DATA_DIR / 'leave_noti_users.json'
leave_noti_users = set(load_json(LEAVE_NOTI_FN, []))   # user ids who want DM when a member leaves
GROUP_SETTING_KEYS['autoapprove'] = 'Auto-approve'

def _uptime_text() -> str:
    secs = int(time.time() - BOT_START)
    d, rem = divmod(secs, 86400)
    hh, rem = divmod(rem, 3600)
    mm, ss = divmod(rem, 60)
    return f"{d}d {hh}h {mm}m {ss}s"

@dp.message(Command('ping'))
async def cmd_ping(msg: types.Message):
    t0 = time.perf_counter()
    sent = await msg.answer("🏓 Pong!")
    latency = (time.perf_counter() - t0) * 1000
    await sent.edit_text(f"🏓 Pong!\n⚡ Latency: {latency:.0f} ms\n⏱️ Uptime: {_uptime_text()}")

def _autoapprove_markup(cid: int) -> InlineKeyboardMarkup:
    on = chat_setting(cid, 'autoapprove')
    return InlineKeyboardMarkup(inline_keyboard=[[
        make_button("✅ Auto-approve: ON" if on else "❌ Auto-approve: OFF",
                    callback_data=f"aa:toggle:{cid}",
                    style=BTN_SUCCESS if on else BTN_DANGER)
    ]])

@dp.message(Command('autoapprove'), F.chat.type.in_(GROUP_TYPES))
async def cmd_autoapprove(msg: types.Message):
    if not await _require_admin(msg):
        return
    await msg.reply("🔁 Auto-approve for this chat. Tap to toggle:",
                    reply_markup=_autoapprove_markup(msg.chat.id))

@dp.callback_query(lambda c: bool(c.data) and c.data.startswith('aa:toggle:'))
async def autoapprove_toggle(cb: CallbackQuery):
    try:
        cid = int(cb.data.split(':')[2])
    except ValueError:
        return await cb.answer("❌ Invalid chat.", show_alert=True)
    if not await is_chat_admin(cid, cb.from_user.id):
        return await cb.answer("⛔ Only admins can change this.", show_alert=True)
    current = group_settings.setdefault(str(cid), {})
    current['autoapprove'] = not chat_setting(cid, 'autoapprove')
    save_json(SETTINGS_FN, group_settings)
    await cb.message.edit_reply_markup(reply_markup=_autoapprove_markup(cid))
    await cb.answer("Saved.")

@dp.message(Command('approve_all'))
async def cmd_approve_all_alias(msg: types.Message):
    """Alias of '/approve all <chat_id>'. In a group, the current chat is used."""
    parts = (msg.text or '').split()
    if msg.chat.type in GROUP_TYPES:
        chat_id = msg.chat.id
        if not await is_chat_admin(chat_id, msg.from_user.id):
            return await msg.reply("❌ Only admins can approve requests here.")
    else:
        if len(parts) < 2 or not parts[1].lstrip('-').isdigit():
            return await msg.answer("Usage: /approve_all &lt;chat_id&gt;  (or run it inside the group)")
        chat_id = int(parts[1])
    await handle_approve_all(msg, chat_id, msg.from_user.id)

@dp.message(Command('leave_noti'), F.chat.type == ChatType.PRIVATE)
async def cmd_leave_noti(msg: types.Message):
    uid = msg.from_user.id
    if uid in leave_noti_users:
        leave_noti_users.discard(uid)
        state = "OFF"
    else:
        leave_noti_users.add(uid)
        state = "ON"
    save_json(LEAVE_NOTI_FN, list(leave_noti_users))
    await msg.answer(f"🔔 Leave notifications: {state}\n(You will get a DM when a member leaves a group where you are admin.)")

async def notify_leave_to_admins(chat, user):
    if not leave_noti_users:
        return
    try:
        admins = await bot.get_chat_administrators(chat.id)
    except Exception:
        return
    text = f"🚪 {h(user.full_name)} left <b>{h(chat.title or '')}</b>."
    for adm in admins:
        if adm.user.id in leave_noti_users:
            try:
                await bot.send_message(adm.user.id, text, parse_mode=ParseMode.HTML)
            except Exception:
                pass

@dp.message(Command('pbroadcast'), F.chat.type == ChatType.PRIVATE)
async def cmd_pbroadcast(msg: types.Message):
    """Broadcast and pin the message in every user's DM."""
    if not is_bot_admin(msg.from_user.id):
        return
    src = msg.reply_to_message
    body = None
    if not src:
        parts = (msg.text or '').split(maxsplit=1)
        if len(parts) < 2:
            return await msg.answer("Usage: reply to a message with /pbroadcast, or /pbroadcast &lt;text&gt;")
        body = parts[1]
    status = await msg.answer("📌 Broadcasting and pinning...")
    ok = fail = 0
    for uid in list(accepted_users):
        try:
            if src:
                mid = (await bot.copy_message(uid, from_chat_id=msg.chat.id, message_id=src.message_id)).message_id
            else:
                mid = (await bot.send_message(uid, body, parse_mode=None)).message_id
            try:
                await bot.pin_chat_message(uid, mid, disable_notification=True)
            except Exception:
                pass  # pinning is best-effort (some DMs may not allow it)
            ok += 1
        except Exception:
            fail += 1
        await asyncio.sleep(0.05)
    await status.edit_text(f"✅ Done. Sent and pinned: {ok}, failed: {fail}")

@dp.message(Command('restart'), F.chat.type == ChatType.PRIVATE)
async def cmd_restart(msg: types.Message):
    """Owner/bot admin restart. Saves state and exits; the host (Render, Docker) restarts the process."""
    if not is_bot_admin(msg.from_user.id):
        return
    save_state()
    await msg.answer("🔄 Restarting... the host will bring the bot back in a few seconds.")
    asyncio.get_running_loop().call_later(2, os._exit, 0)


# ================= OWNER / ADMIN PANEL, FORCE-SUB MANAGEMENT, PENDING, DM WELCOME =================
@dp.message(Command('setdmwelcome'), F.chat.type.in_(GROUP_TYPES))
async def cmd_set_dm_welcome(msg: types.Message):
    """Text sent in private DM to users whose join request was approved. Placeholders: {mention} {first} {chat}."""
    if not await _require_admin(msg):
        return
    parts = (msg.text or '').split(maxsplit=1)
    if len(parts) < 2:
        return await msg.reply("Usage: /setdmwelcome &lt;text&gt;  (placeholders: {mention} {first} {chat}, HTML allowed). Use 'off' to reset.")
    chat_s = group_settings.setdefault(str(msg.chat.id), {})
    if parts[1].strip().lower() == 'off':
        chat_s.pop('dm_welcome_text', None)
        await msg.reply("✅ DM welcome reset to default.")
    else:
        chat_s['dm_welcome_text'] = parts[1]
        await msg.reply("✅ DM welcome text saved.")
    save_json(SETTINGS_FN, group_settings)

@dp.message(Command('setwelcomebuttons'), F.chat.type.in_(GROUP_TYPES))
async def cmd_set_welcome_buttons(msg: types.Message):
    """One button per line: Text | https://url | color   (color: primary, success or danger)."""
    if not await _require_admin(msg):
        return
    body = (msg.text or '').split(maxsplit=1)
    chat_s = group_settings.setdefault(str(msg.chat.id), {})
    if len(body) < 2 or body[1].strip().lower() == 'off':
        chat_s.pop('dm_welcome_buttons', None)
        save_json(SETTINGS_FN, group_settings)
        return await msg.reply("✅ DM welcome buttons cleared.")
    buttons = []
    for line in body[1].splitlines():
        bits = [b.strip() for b in line.split('|')]
        if len(bits) < 2 or not bits[1].startswith(('http://', 'https://', 'tg://')):
            continue
        color = bits[2].lower() if len(bits) > 2 and bits[2].lower() in ('primary', 'success', 'danger') else None
        buttons.append([bits[0], bits[1], color])
    chat_s['dm_welcome_buttons'] = buttons
    save_json(SETTINGS_FN, group_settings)
    await msg.reply(f"✅ Saved {len(buttons)} welcome button(s).")

@dp.message(Command('pending'), F.chat.type.in_(GROUP_TYPES))
async def cmd_pending(msg: types.Message):
    if not await _require_admin(msg):
        return
    ids = await fetch_pending_user_ids(msg.chat.id, limits.get(str(msg.chat.id), {}))
    if not ids:
        return await msg.reply("No pending join requests (or no logged-in admin session can read them).")
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        make_button(f"✅ Approve all ({len(ids)})", callback_data=f"pend:all:{msg.chat.id}", style=BTN_SUCCESS),
        make_button("❌ Decline all", callback_data=f"pend:dec:{msg.chat.id}", style=BTN_DANGER),
    ]])
    await msg.reply(f"⏳ Pending join requests: {len(ids)}", reply_markup=kb)

@dp.callback_query(lambda c: bool(c.data) and c.data.startswith('pend:all:'))
async def pending_approve_all(cb: CallbackQuery):
    cid = int(cb.data.split(':')[2])
    if not await is_chat_admin(cid, cb.from_user.id):
        return await cb.answer("⛔ Admins only.", show_alert=True)
    await cb.answer("Approving...")
    ids = await fetch_pending_user_ids(cid, limits.get(str(cid), {}))
    done = await approve_users(cid, ids, limits.get(str(cid), {}))
    for uid in done:
        await notify_approved(cid, uid)
    await cb.message.edit_text(f"✅ Approved {len(done)} of {len(ids)} pending request(s).")

@dp.message(Command('fjoin'), F.chat.type == ChatType.PRIVATE)
async def cmd_fjoin(msg: types.Message):
    if not is_bot_admin(msg.from_user.id):
        return
    parts = (msg.text or '').split()
    if len(parts) >= 2 and parts[1].lower() == 'list' or len(parts) == 1:
        if not FORCE_SUB_CHANNELS:
            return await msg.answer("No force-sub channels set.\nAdd: /fjoin add &lt;chat_id&gt; &lt;invite_url&gt;")
        lines = "\n".join(f"• <code>{c['id']}</code> — {h(c['url'])}" for c in FORCE_SUB_CHANNELS)
        return await msg.answer("📢 Force-sub channels:\n" + lines, parse_mode=ParseMode.HTML)
    if parts[1].lower() == 'add' and len(parts) >= 4 and parts[2].lstrip('-').isdigit():
        cid = int(parts[2])
        FORCE_SUB_CHANNELS[:] = [c for c in FORCE_SUB_CHANNELS if c['id'] != cid] + [{'id': cid, 'url': parts[3]}]
        save_json(FSUB_FN, FORCE_SUB_CHANNELS)
        return await msg.answer(f"✅ Force-sub channel <code>{cid}</code> added.", parse_mode=ParseMode.HTML)
    if parts[1].lower() == 'remove' and len(parts) >= 3 and parts[2].lstrip('-').isdigit():
        cid = int(parts[2])
        FORCE_SUB_CHANNELS[:] = [c for c in FORCE_SUB_CHANNELS if c['id'] != cid]
        save_json(FSUB_FN, FORCE_SUB_CHANNELS)
        return await msg.answer(f"✅ Removed <code>{cid}</code>.", parse_mode=ParseMode.HTML)
    await msg.answer("Usage:\n/fjoin list\n/fjoin add &lt;chat_id&gt; &lt;invite_url&gt;\n/fjoin remove &lt;chat_id&gt;")

@dp.message(Command('chats'), F.chat.type == ChatType.PRIVATE)
async def cmd_chats(msg: types.Message):
    if not is_bot_admin(msg.from_user.id):
        return
    if not groups:
        return await msg.answer("No connected chats yet.")
    lines = "\n".join(f"• {h(str(t))} — <code>{c}</code>" for c, t in list(groups.items())[:100])
    await msg.answer(f"📡 Connected chats: {len(groups)}\n{lines}", parse_mode=ParseMode.HTML)

def _admin_panel_markup() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [make_button("📊 Stats", callback_data="adm:stats", style=BTN_PRIMARY),
         make_button("📡 Chats", callback_data="adm:chats", style=BTN_PRIMARY)],
        [make_button("👥 Users", callback_data="adm:users", style=BTN_PRIMARY),
         make_button("📢 Force-sub", callback_data="adm:fsub", style=BTN_PRIMARY)],
    ])

@dp.message(Command('admin'), F.chat.type == ChatType.PRIVATE)
async def cmd_admin_panel(msg: types.Message):
    if not is_bot_admin(msg.from_user.id):
        return
    await msg.answer("🛠 <b>Admin control panel</b>", reply_markup=_admin_panel_markup(), parse_mode=ParseMode.HTML)

@dp.callback_query(lambda c: bool(c.data) and c.data.startswith('adm:'))
async def admin_panel_callback(cb: CallbackQuery):
    if not is_bot_admin(cb.from_user.id):
        return await cb.answer("⛔ Admins only.", show_alert=True)
    action = cb.data.split(':', 1)[1]
    await cb.answer()
    if action == 'stats':
        active = sum(1 for v in user_sessions.values() if v.get('is_active'))
        text = (f"📊 <b>Bot stats</b>\\nUsers: {len(accepted_users)}\\nChats: {len(groups)}\\n"
                f"Logged-in accounts: {active}\\nChats with a mode: {len(limits)}\\nMonthly active users: {active_users_within(30)}")
    elif action == 'chats':
        text = "📡 Chats: " + (str(len(groups)) if groups else "none") + "\\n" + "\\n".join(f"• {h(str(t))} — <code>{c}</code>" for c, t in list(groups.items())[:30])
    elif action == 'users':
        text = f"👥 Users: {len(accepted_users)}"
    else:
        text = ("📢 Force-sub: " + (str(len(FORCE_SUB_CHANNELS)) + " channel(s)") if FORCE_SUB_CHANNELS else "📢 Force-sub: none set")
    await cb.message.answer(text, parse_mode=ParseMode.HTML)

ABOUT_TEXT = (
    f"💠 {to_small_caps('About This Bot')} 💠\n\n"
    f"╭────[ ✨ {to_small_caps('Anuj')} ]────⍟\n"
    f"├⍟ 🚀 {to_small_caps('Bot Name')}  : {to_small_caps('Auto Approval Bot')}\n"
    f"├⍟ 👨‍💻 {to_small_caps('Developer')}  : <a href=\"https://t.me/anujedits76\">{to_small_caps('Anuj Kumar')}</a>\n"
    f"├⍟ 🔗 {to_small_caps('Library')}  : <a href=\"https://github.com/aiogram/aiogram\">{to_small_caps('aiogram')}</a>\n"
    f"├⍟ ⚡️ {to_small_caps('Language')}  : <a href=\"https://www.python.org/\">{to_small_caps('Python')} 3.11+</a>\n"
    f"├⍟ ⚙️ {to_small_caps('Database')}  : {to_small_caps('JSON or MongoDB')}\n"
    f"├⍟ ⭐️ {to_small_caps('Hosting')}  :  {to_small_caps('Render / VPS / Docker')}\n"
    "╰───────────────⍟"
)

def about_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[make_button("❌ Close", callback_data="about_close", style=BTN_DANGER)]])

PRIVACY_TEXT_SHORT = (
    "🔒 <b>Privacy</b>\n\n"
    "Stored: your Telegram user ID (to send welcome DMs and broadcasts), chat IDs and titles and settings "
    "of groups where the bot is added, and counts of approved requests.\n\n"
    "If you log in with /login, your session string is stored to approve requests for you. "
    "Use /logout to remove it.\n\n"
    "Messages and media are not collected beyond what the commands need. Data is not sold or shared."
)

@dp.message(Command('about'))
async def cmd_about(msg: types.Message):
    await msg.answer(ABOUT_TEXT, reply_markup=about_keyboard(), parse_mode=ParseMode.HTML,
                     link_preview_options=types.LinkPreviewOptions(is_disabled=True))

@dp.callback_query(lambda c: c.data == 'about_close')
async def about_close_cb(cb: CallbackQuery):
    try:
        await cb.message.delete()
    except Exception:
        pass
    await cb.answer()

@dp.message(Command('privacy'))
async def cmd_privacy(msg: types.Message):
    await msg.answer(PRIVACY_TEXT_SHORT, parse_mode=ParseMode.HTML)


async def decline_users(chat_id: int, user_ids, cfg: dict = None) -> list:
    """Decline pending join requests: bot first, then a logged-in admin session."""
    owner = (cfg or {}).get('owner_id')
    declined = []
    session = None
    for uid in user_ids:
        try:
            await bot.decline_chat_join_request(chat_id, uid)
            declined.append(uid)
            continue
        except Exception:
            pass
        if session is None:
            client, peer = await open_session_client(chat_id, owner)
            session = (client, peer) if client else False
        if session:
            try:
                from telethon.tl.functions.messages import HideChatJoinRequestRequest
                target = _pending_input_users.get(uid) or await session[0].get_input_entity(uid)
                await session[0](HideChatJoinRequestRequest(peer=session[1], user_id=target, approved=False))
                declined.append(uid)
            except Exception as e:
                logging.warning(f"Session decline failed for {uid}: {e}")
        await asyncio.sleep(0.5)
    if session:
        await session[0].disconnect()
    return declined

@dp.callback_query(lambda c: bool(c.data) and c.data.startswith('pend:dec:'))
async def pending_decline_all(cb: CallbackQuery):
    cid = int(cb.data.split(':')[2])
    if not await is_chat_admin(cid, cb.from_user.id):
        return await cb.answer("⛔ Admins only.", show_alert=True)
    await cb.answer("Declining...")
    ids = await fetch_pending_user_ids(cid, limits.get(str(cid), {}))
    done = await decline_users(cid, ids, limits.get(str(cid), {}))
    await cb.message.edit_text(f"❌ Declined {len(done)} of {len(ids)} pending request(s).")

@dp.message(Command('nmod', 'mode1d'), F.chat.type == ChatType.PRIVATE)
async def cmd_mode_switch(msg: types.Message):
    """/nmod <chat_id> = auto-accept mode; /mode1d <chat_id> = manual mode (requests stay pending)."""
    parts = (msg.text or '').split()
    cmd = parts[0].lower().lstrip('/').split('@')[0]
    if len(parts) < 2 or not parts[1].lstrip('-').isdigit():
        return await msg.answer(f"Usage: /{cmd} &lt;chat_id&gt;")
    cid = int(parts[1])
    if not await is_chat_admin(cid, msg.from_user.id):
        return await msg.answer("❌ You must be an admin of that chat.")
    group_settings.setdefault(str(cid), {})['autoapprove'] = (cmd == 'nmod')
    save_json(SETTINGS_FN, group_settings)
    if cmd == 'nmod':
        await msg.answer(f"✅ Auto-accept mode ON for <code>{cid}</code>.", parse_mode=ParseMode.HTML)
    else:
        await msg.answer(f"✅ Manual mode for <code>{cid}</code>. New requests stay in the pending queue.", parse_mode=ParseMode.HTML)


@dp.callback_query(lambda c: c.data in ('wel:about', 'wel:help'))
async def welcome_buttons(cb: CallbackQuery):
    if cb.data == 'wel:about':
        await cb.message.answer(ABOUT_TEXT, reply_markup=about_keyboard(), parse_mode=ParseMode.HTML,
                                link_preview_options=types.LinkPreviewOptions(is_disabled=True))
    else:
        await cb.message.answer(HELP_TEXT, parse_mode=ParseMode.HTML, reply_markup=help_keyboard(),
                                link_preview_options=types.LinkPreviewOptions(is_disabled=True))
    await cb.answer()


@dp.callback_query(lambda c: c.data in ('help:back', 'help:close'))
async def help_buttons(cb: CallbackQuery):
    if cb.data == 'help:close':
        try:
            await cb.message.delete()
        except Exception:
            pass
    else:
        send_welcome_to_user(cb.from_user.id)
    await cb.answer()

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
        BotCommand(command="help", description="📖 Help & command list"),
        BotCommand(command="groups", description="🛠 Manage your groups"),
        BotCommand(command="feedback", description="💬 Send feedback"),
        BotCommand(command="ping", description="🏓 Check bot latency and uptime"),
        BotCommand(command="autoapprove", description="🔁 Toggle auto-approve in a group"),
        BotCommand(command="approve_all", description="✅ Approve all pending join requests"),
        BotCommand(command="leave_noti", description="🔔 Toggle leave notifications"),
        BotCommand(command="pending", description="⏳ Check pending join requests"),
        BotCommand(command="nmod", description="⚡ Auto-accept mode for a chat"),
        BotCommand(command="mode1d", description="🕓 Manual mode for a chat"),
        BotCommand(command="about", description="ℹ️ About this bot"),
        BotCommand(command="privacy", description="🔒 Privacy"),
    ]
    await bot.set_my_commands(commands)
    print("✅ Bot commands menu registered!")
    
    await start_health_server()
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
