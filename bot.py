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
from aiogram.dispatcher.middlewares.base import BaseMiddleware
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, FSInputFile, ChatPermissions, BufferedInputFile
import csv, io
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
MONGO_URI = os.getenv('MONGO_URI', 'mongodb+srv://Anujedit:Anujedit@cluster0.7cs2nhd.mongodb.net/?appName=Cluster0')
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
    "≡ <b>{maint}</b> | <a href=\"https://t.me/anujedits76\">{dev}</a>"
)
WELCOME_DESC = (
    "Auto-approve join requests in your groups and channels.\n"
    "Add me as admin and give Add members / Invite users permission."
)

def build_welcome_text(first_name: str) -> str:
    return (
        f"<b>{to_small_caps('hello')} {h(first_name)}! 👋</b>\n\n"
        + WELCOME_BODY.format(desc=h(WELCOME_DESC), maint=to_small_caps('powered by'),
                                              dev=to_small_caps('Anuj Kumar'))
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
        [make_button('⚙️ SETTINGS', callback_data='wel:settings', style=BTN_SUCCESS)],
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

@dp.error()
async def global_error_handler(event):
    exc = event.exception
    if isinstance(exc, TelegramBadRequest) and 'not modified' in str(exc).lower():
        return True            # the message already shows this state; nothing to do
    if isinstance(exc, TelegramForbiddenError):
        return True            # user blocked the bot / cannot be messaged
    logging.error(f"Unhandled bot error: {exc}")
    return True

# ---- Blockquote on every bot message that is sent as HTML ----
from aiogram.client.session.middlewares.base import BaseRequestMiddleware

QUOTE_MAX = 3800   # Telegram text limit is 4096; keep room for the tags

def _quote_html(text):
    """Wrap HTML text in a blockquote once (skips messages that already have one or are too long)."""
    if not isinstance(text, str) or not text.strip() or '<blockquote' in text or len(text) > QUOTE_MAX:
        return text
    return f"<blockquote>{text}</blockquote>"

class QuoteMiddleware(BaseRequestMiddleware):
    """Adds a blockquote to outgoing HTML text and captions. Plain-text messages are left as they are."""
    TEXT_METHODS = ('SendMessage', 'EditMessageText')
    CAPTION_METHODS = ('SendPhoto', 'SendVideo', 'SendAnimation', 'SendDocument', 'SendAudio', 'SendVoice',
                       'EditMessageCaption')

    async def __call__(self, make_request, bot, method):
        name = type(method).__name__
        mode = getattr(method, 'parse_mode', None)
        if mode is not None and str(mode).upper().endswith('HTML'):
            if name in self.TEXT_METHODS and getattr(method, 'text', None):
                method.text = _quote_html(method.text)
            elif name in self.CAPTION_METHODS and getattr(method, 'caption', None):
                method.caption = _quote_html(method.caption)
        return await make_request(bot, method)

bot.session.middleware(QuoteMiddleware())

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
        if evt.from_user and evt.from_user.id:
            group_settings.setdefault('_owners', {})[cid] = evt.from_user.id
            save_json(SETTINGS_FN, group_settings)
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
        pic = banner_url() or pic
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
    if is_banned(uid):
        await msg.answer("🚫 You are banned from using this bot.", parse_mode=None)
        return
    if is_maintenance() and not is_bot_admin(uid):
        await msg.answer("🛠 The bot is under maintenance. Please try again later.", parse_mode=None)
        return
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
        accepted_users.add(uid)   # registered automatically (used for broadcasts)
        save_state()
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
        "👨🏻‍💻 Dev : <a href='https://t.me/anujedits76'>ᴀɴᴜᴊ ᴋᴜᴍᴀʀ</a>",
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
                "👨🏻‍💻 Dev : <a href='https://t.me/anujedits76'>ᴀɴᴜᴊ ᴋᴜᴍᴀʀ</a>",
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
                "👨🏻‍💻 Dev : <a href='https://t.me/anujedits76'>ᴀɴᴜᴊ ᴋᴜᴍᴀʀ</a>",
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
            parse_mode=ParseMode.HTML
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
            parse_mode=ParseMode.HTML
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
                "👨🏻‍💻 Dev : <a href='https://t.me/anujedits76'>ᴀɴᴜᴊ ᴋᴜᴍᴀʀ</a>",
                parse_mode=ParseMode.HTML
            )
            
        except SessionPasswordNeededError:
            # 2FA required
            await state.set_state(LoginStates.waiting_for_password)
            await status_msg.edit_text(
                f"🔒 <b>{to_small_caps('your account has 2fa enabled. send your password')}</b>\n\n"
                f"⚠️ <b>{to_small_caps('important: your password is case-sensitive')}</b>\n\n"
                f"/cancel - {to_small_caps('cancel the process')}\n\n"
                "👨🏻‍💻 Dev : <a href='https://t.me/anujedits76'>ᴀɴᴜᴊ ᴋᴜᴍᴀʀ</a>",
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
                    "👨🏻‍💻 Dev : <a href='https://t.me/anujedits76'>ᴀɴᴜᴊ ᴋᴜᴍᴀʀ</a>",
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
            "👨🏻‍💻 Dev : <a href='https://t.me/anujedits76'>ᴀɴᴜᴊ ᴋᴜᴍᴀʀ</a>",
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
                "👨🏻‍💻 Dev : <a href='https://t.me/anujedits76'>ᴀɴᴜᴊ ᴋᴜᴍᴀʀ</a>",
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
            "👨🏻‍💻 Dev : <a href='https://t.me/anujedits76'>ᴀɴᴜᴊ ᴋᴜᴍᴀʀ</a>",
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
                        caption=f"📄 {file_desc}\n👨🏻‍💻 Dev : <a href='https://t.me/anujedits76'>ᴀɴᴜᴊ ᴋᴜᴍᴀʀ</a>"
                    )
                except Exception as e:
                    logging.error(f"Error sending {file_desc}: {e}")
        
        await msg.answer(
            "✅ Data export completed!\n\n"
            "👨🏻‍💻 Dev : <a href='https://t.me/anujedits76'>ᴀɴᴜᴊ ᴋᴜᴍᴀʀ</a>",
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
        stop_flags.discard(chat_id)
        try:
            await status_msg.edit_text(f"⚡ Approving {len(ids)} request(s)...", reply_markup=stop_markup(chat_id),
                                       parse_mode=None)
        except Exception:
            pass
        for uid in ids:
            if chat_id in stop_flags:
                break
            if await session_approve(client, peer, uid):
                approved_count += 1
                await asyncio.sleep(0.5)  # Rate limit protection
        stopped = chat_id in stop_flags
        stop_flags.discard(chat_id)

        chat_name = await get_chat_name(chat_id)
        await status_msg.edit_text(
            f"{'⛔ Stopped' if stopped else '✅ Approved'} {approved_count} members in {h(chat_name)}\n\n"
            f"👨🏻‍💻 Dev : <a href='https://t.me/anujedits76'>ᴀɴᴜᴊ ᴋᴜᴍᴀʀ</a>"
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
            f"👨🏻‍💻 Dev : <a href='https://t.me/anujedits76'>ᴀɴᴜᴊ ᴋᴜᴍᴀʀ</a>"
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
            "👨🏻‍💻 Dev : <a href='https://t.me/anujedits76'>ᴀɴᴜᴊ ᴋᴜᴍᴀʀ</a>",
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
            logged_out_text = APPROVE_WELCOME_TEXT + "\n\n🔴 Status: Logged Out"
            try:
                await cb.message.edit_caption(caption=logged_out_text, reply_markup=kb, parse_mode=None)
            except Exception:
                # the panel was sent as plain text (photo fallback), so edit the text instead
                await cb.message.edit_text(logged_out_text, reply_markup=kb, parse_mode=None)
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
    f"📖 <b>{h(to_small_caps('help & commands'))}</b>\n\n"
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
        [make_button("⚙️ SETTINGS", callback_data="wel:settings", style=BTN_SUCCESS)],
        [make_button("🧭 SETUP GUIDE", callback_data="setup:1", style=BTN_PRIMARY)],
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
    for _ in range(len(user_ids) - len(approved)):
        record_failure('approve_failed')
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
    clear_pending_req(chat_id, uid)
    count_approval(chat_id)
    user_approvals[str(uid)] = user_approvals.get(str(uid), 0) + 1
    save_json(USER_APPR_FN, user_approvals)
    await log_event(f"✅ Approved <code>{uid}</code> in <code>{chat_id}</code>.")
    if not chat_setting(chat_id, 'dm_welcome'):
        return  # approval DM switched off for this chat
    try:
        chat_title = await get_chat_name(chat_id)
        username = None
        try:
            ucht = await bot.get_chat(uid)
            full, username = ucht.full_name, ucht.username
        except Exception:
            full = "there"
        custom = group_settings.get(str(chat_id), {}).get('dm_welcome_text')
        if custom:
            body, text_buttons = split_inline_buttons(custom)
            text = render_dm_placeholders(body, full, username, chat_title, uid)
            kb = text_buttons or dm_welcome_markup(chat_id)
            parse = ParseMode.HTML
        else:
            text = (
                f"Hey {full}!!\n"
                f"Your request to join {chat_title} has been approved.\n"
                "Join Request approval Services.\n"
                "Click /start for more info."
            )
            kb, parse = None, None
        # Every approval (single or bulk) comes with a random picture
        sent = None
        try:
            media = _dm_media(chat_id)
            media_kind = group_settings.get(str(chat_id), {}).get('dm_welcome_media_type')
            if media and media_kind == 'video':
                sent = await bot.send_video(uid, video=media, caption=text, reply_markup=kb, parse_mode=parse)
            elif media and media_kind == 'animation':
                sent = await bot.send_animation(uid, animation=media, caption=text, reply_markup=kb, parse_mode=parse)
            elif media:
                sent = await bot.send_photo(uid, photo=media, caption=text, reply_markup=kb, parse_mode=parse)
            else:
                sent = await send_random_pic(uid, text, reply_markup=kb, parse_mode=parse)
        except TelegramForbiddenError:
            raise
        except Exception as e:
            logging.warning(f"Approval photo failed for user {uid}: {e}")
            sent = await bot.send_message(uid, text, reply_markup=kb, parse_mode=parse)
        delete_after = int(group_settings.get(str(chat_id), {}).get('dm_delete_after', 0) or 0)
        if sent and delete_after > 0:
            task = asyncio.create_task(_delete_later(sent, delete_after))
            _background_tasks.add(task)
            task.add_done_callback(_background_tasks.discard)
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
    if chat_setting(chat_id, 'sendonly'):
        delay = group_settings.get(str(chat_id), {}).get('sendonly_delay', 86400)
        delayed_queue.append({'chat': chat_id, 'uid': uid, 'due': time.time() + delay})
        save_json(DELAYED_FN, delayed_queue)
        return  # held: the delayed worker approves it when the timer is up
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

async def captcha_timeout(chat_id: int, uid: int, seconds: float = CAPTCHA_TIMEOUT_SECONDS):
    try:
        await asyncio.sleep(max(0, seconds))
    except asyncio.CancelledError:
        return
    _captcha_tasks.pop((chat_id, uid), None)
    captcha_pending.pop(f"{chat_id}:{uid}", None)
    save_json(CAPTCHA_FN, captcha_pending)
    try:
        clear_pending_req(chat_id, uid)
        await bot.decline_chat_join_request(chat_id, uid)
        await bot.send_message(uid, "⏱️ Verification time expired. Send a new join request to try again.", parse_mode=None)
    except Exception as e:
        logging.warning(f"Captcha timeout handling failed for {uid} in {chat_id}: {e}")
    record_failure('captcha_timeout')
    suspect[str(uid)] = suspect.get(str(uid), 0) + 1
    save_json(SUSPECT_FN, suspect)
    await log_event(f"⏱️ Captcha expired for <code>{uid}</code> in <code>{chat_id}</code>; request declined.")

@dp.chat_join_request()
async def handle_join_request(req: types.ChatJoinRequest):
    chat_id, uid = req.chat.id, req.from_user.id
    if is_chan_banned(chat_id):
        return  # banned chat: the bot ignores its requests
    set_pending_req(chat_id, uid)
    if is_maintenance():
        return  # requests stay pending while maintenance is on
    if is_banned(uid):
        try:
            clear_pending_req(chat_id, uid)
            await bot.decline_chat_join_request(chat_id, uid)
        except Exception:
            pass
        record_failure('banned_user')
        return
    if chat_setting(chat_id, 'autoreject'):
        try:
            await decline_users(chat_id, [uid], limits.get(str(chat_id), {}))
        except Exception as e:
            logging.warning(f"Auto-reject failed for {uid} in {chat_id}: {e}")
        record_failure('auto_rejected')
        await log_event(f"⛔ Auto-rejected <code>{uid}</code> in <code>{chat_id}</code>.")
        return
    # Verified-user check: optionally require a Telegram username before approval
    if chat_setting(chat_id, 'require_username') and not req.from_user.username:
        try:
            clear_pending_req(chat_id, uid)
            await bot.decline_chat_join_request(chat_id, uid)
        except Exception as e:
            logging.warning(f"Could not decline {uid} (no username): {e}")
        try:
            await bot.send_message(uid, "❌ Your request was declined: this group needs a Telegram username. Set one and request again.", parse_mode=None)
        except Exception:
            pass
        record_failure('no_username')
        await log_event(f"🚫 Declined <code>{uid}</code> (no username) in <code>{chat_id}</code>.")
        return
    if not CAPTCHA_JOIN_PROTECTION or not chat_setting(chat_id, 'captcha'):
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
    expires = time.time() + CAPTCHA_TIMEOUT_SECONDS
    captcha_pending[f"{chat_id}:{uid}"] = {"chat": chat_id, "uid": uid, "expires": expires}
    save_json(CAPTCHA_FN, captcha_pending)
    _captcha_tasks[(chat_id, uid)] = asyncio.create_task(captcha_timeout(chat_id, uid, CAPTCHA_TIMEOUT_SECONDS))

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
    captcha_pending.pop(f"{chat_id}:{uid}", None)
    save_json(CAPTCHA_FN, captcha_pending)
    await log_event(f"🤖 Captcha passed by <code>{uid}</code> in <code>{chat_id}</code>.")
    await cb.answer("✅ Verification complete! You are approved.", show_alert=True)
    await route_join_request(chat_id, uid)

# ---------- Multi force-sub ----------
async def missing_force_sub(uid: int) -> list:
    missing = []
    for ch in FORCE_SUB_CHANNELS:
        try:
            member = await bot.get_chat_member(ch['id'], uid)
            if member.status in (ChatMemberStatus.LEFT, ChatMemberStatus.KICKED):
                if has_pending_req(ch['id'], uid):
                    continue  # join request sent and waiting: counts as subscribed
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
        text, kb = await build_fsub_gate(cb.from_user)
        try:
            await cb.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)
        except Exception:
            pass
        return
    await cb.answer("✅ Thanks for joining!")
    try:
        await cb.message.delete()
    except Exception:
        pass
    if uid not in accepted_users:
        accepted_users.add(uid)
        save_state()
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
    await log_event(f"🚪 <code>{user.id}</code> left <code>{msg.chat.id}</code>.")
    asyncio.create_task(notify_leave_to_admins(msg.chat, user))
    asyncio.create_task(send_leave_dm(msg.chat, user))
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
    default = {'antispam': False, 'require_username': False, 'autoreject': False, 'sendonly': False}.get(key, True)
    return bool(group_settings.get(str(chat_id), {}).get(key, default))

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
        await log_event(f"🚫 Banned <code>{target.id}</code> in <code>{msg.chat.id}</code> by <code>{msg.from_user.id}</code>.")
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
        await log_event(f"👢 Kicked <code>{target.id}</code> from <code>{msg.chat.id}</code> by <code>{msg.from_user.id}</code>.")
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

    # Anti-spam: links from members who joined recently, link/mention floods, forwards
    if chat_setting(msg.chat.id, 'antispam'):
        links = len(re.findall(r'https?://|t\.me/|www\.', text, re.I))
        mentions = len(re.findall(r'@\w{3,}', text))
        joined = join_times.get(f"{msg.chat.id}:{msg.from_user.id}")
        new_member = joined is not None and (time.time() - joined) < 86400
        if (new_member and links) or links >= 3 or mentions >= 5 or msg.forward_date:
            try:
                await msg.delete()
            except Exception:
                pass
            return

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
        f"🏁 All-time approvals: {all_time_approvals()}\n"
        f"🐍 Python: {python_info()}\n"
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
                     parse_mode=ParseMode.HTML,
                     reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                         make_button("🧹 Drop unjoined from broadcast list", callback_data="unj:drop", style=BTN_DANGER)]]))


# ================= ALL REMAINING FEATURES =================
GROUP_WELCOME_ENABLED = True

@dp.message(F.new_chat_members, F.chat.type.in_(GROUP_TYPES))
async def group_welcome(msg: types.Message):
    for user in msg.new_chat_members:
        join_times[f"{msg.chat.id}:{user.id}"] = time.time()
        await log_event(f"➕ <code>{user.id}</code> joined <code>{msg.chat.id}</code>.")
    save_json(JOIN_FN, join_times)
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
    """Preview, then confirm (Send / Cancel) with an optional auto-delete timer."""
    if not is_bot_admin(msg.from_user.id):
        return
    await _start_broadcast(msg, pin=False)

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
        on = chat_setting(cid, key)
        rows.append([make_button(f"{label}: {'✅ On' if on else '❌ Off'}", callback_data=f"grp:toggle:{key}:{cid}",
                                 style=BTN_SUCCESS if on else BTN_DANGER)])
    active = locks.get(str(cid), [])
    for kind, label in LOCK_LABELS.items():
        on = kind in active
        rows.append([make_button(f"🔒 Lock {label}: {'ON' if on else 'OFF'}", callback_data=f"grp:toggle:lock_{kind}:{cid}",
                                 style=BTN_SUCCESS if on else BTN_DANGER)])
    stale = int(group_settings.get(str(cid), {}).get('stale_hours', 0) or 0)
    rows.append([make_button(f"🧹 Stale request cleanup: {str(stale) + ' h' if stale else 'OFF'}",
                             callback_data=f"grp:toggle:stale:{cid}", style=BTN_SUCCESS if stale else BTN_DANGER)])
    dmdel = int(group_settings.get(str(cid), {}).get('dm_delete_after', 0) or 0)
    rows.append([make_button(f"🗑 Approval DM auto-delete: {'5 min' if dmdel else 'never'}",
                             callback_data=f"grp:toggle:dmdel:{cid}", style=BTN_SUCCESS if dmdel else BTN_DANGER)])
    perms = group_settings.get(str(cid), {}).get('chatperms', 'open')
    rows.append([make_button(f"🔐 Member permissions: {perms} (tap to change)",
                             callback_data=f"grp:perms:{cid}", style=BTN_PRIMARY)])
    banned = is_chan_banned(cid)
    rows.append([make_button(f"⛔ Bot ignores this chat: {'ON' if banned else 'OFF'}",
                             callback_data=f"grp:toggle:chanban:{cid}", style=BTN_DANGER if banned else BTN_SUCCESS)])
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
    await msg.answer("🛠 <b>Select a group to manage:</b>", reply_markup=_groups_page_markup(gs, 0), parse_mode=ParseMode.HTML)

@dp.callback_query(lambda c: bool(c.data) and c.data.startswith('grp:'))
async def group_panel_callback(cb: CallbackQuery):
    parts = cb.data.split(':')
    action = parts[1]
    if action == 'noop':
        return await cb.answer()
    if action == 'list':
        # grp:list:<page> (paging) and grp:list (page 1) both land here: honour the page number
        page = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 0
        gs = await _admin_groups(cb.from_user.id)
        if not gs:
            await cb.answer("No groups.")
            return await cb.message.edit_text("You are not an admin of any registered group yet.")
        await cb.message.edit_text("🛠 <b>Select a group to manage:</b>", reply_markup=_groups_page_markup(gs, page), parse_mode=ParseMode.HTML)
        return await cb.answer()
    try:
        cid = int(parts[-1])
    except ValueError:
        return await cb.answer("❌ Invalid group.", show_alert=True)
    if not await is_chat_admin(cid, cb.from_user.id):
        return await cb.answer("⛔ You are not an admin of that group.", show_alert=True)
    if action == 'toggle' and len(parts) == 4 and parts[2] == 'stale':
        chat_s = group_settings.setdefault(str(cid), {})
        chat_s['stale_hours'] = 0 if int(chat_s.get('stale_hours', 0) or 0) else 48
        save_json(SETTINGS_FN, group_settings)
    elif action == 'toggle' and len(parts) == 4 and parts[2] == 'dmdel':
        chat_s = group_settings.setdefault(str(cid), {})
        chat_s['dm_delete_after'] = 0 if int(chat_s.get('dm_delete_after', 0) or 0) else 300
        save_json(SETTINGS_FN, group_settings)
    elif action == 'perms' and len(parts) == 3:
        order = ['open', 'nomedia', 'lock']
        cur = group_settings.get(str(cid), {}).get('chatperms', 'open')
        nxt = order[(order.index(cur) + 1) % len(order)] if cur in order else 'open'
        try:
            await bot.set_chat_permissions(cid, CHAT_PERMS[nxt])
        except Exception as e:
            return await cb.answer(f"Could not change permissions: {str(e)[:150]}", show_alert=True)
        group_settings.setdefault(str(cid), {})['chatperms'] = nxt
        save_json(SETTINGS_FN, group_settings)
    if action == 'toggle' and len(parts) == 4 and parts[2] == 'chanban':
        if is_chan_banned(cid):
            chan_bans.pop(str(cid), None)
        else:
            chan_bans[str(cid)] = 'set from group panel'
        save_json(CHAN_BANS_FN, chan_bans)
    if action == 'toggle' and len(parts) == 4:
        key = parts[2]
        if key.startswith('lock_') and key[5:] in LOCK_LABELS:
            kind = key[5:]
            current_locks = set(locks.get(str(cid), []))
            current_locks.symmetric_difference_update({kind})
            locks[str(cid)] = sorted(current_locks)
            save_json(LOCKS_FN, locks)
        elif key in GROUP_SETTING_KEYS:
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
    m = re.fullmatch(r'(\d+)([smhdw])', (token or '').lower())
    if not m:
        return None
    return int(m.group(1)) * {'s': 1, 'm': 60, 'h': 3600, 'd': 86400, 'w': 604800}[m.group(2)]

@dp.message(Command('welcome', 'goodbye', 'antiflood', 'autoreject'), F.chat.type.in_(GROUP_TYPES))
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
    """Preview, then confirm; the message is pinned in every user's DM."""
    if not is_bot_admin(msg.from_user.id):
        return
    await _start_broadcast(msg, pin=True)

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
    chat_s = group_settings.setdefault(str(msg.chat.id), {})
    rmsg = msg.reply_to_message
    media_id, media_kind = None, None
    if rmsg and rmsg.photo:
        media_id, media_kind = rmsg.photo[-1].file_id, 'photo'
    elif rmsg and rmsg.animation:
        media_id, media_kind = rmsg.animation.file_id, 'animation'
    elif rmsg and rmsg.video:
        media_id, media_kind = rmsg.video.file_id, 'video'
    if media_id:
        chat_s['dm_welcome_media'] = media_id
        chat_s['dm_welcome_media_type'] = media_kind
        await msg.reply(f"✅ DM welcome {media_kind} saved." + (" Text unchanged." if len(parts) < 2 else ""))
        if len(parts) >= 2:
            chat_s['dm_welcome_text'] = parts[1]
            await msg.reply("✅ DM welcome text saved too.")
    elif len(parts) < 2:
        return await msg.reply("Usage: /setdmwelcome &lt;text&gt;  (placeholders: {mention} {first} {chat}, HTML allowed). Reply to a photo to add a picture. Use 'off' to reset.")
    elif parts[1].strip().lower() == 'off':
        chat_s.pop('dm_welcome_text', None)
        chat_s.pop('dm_welcome_media', None)
        chat_s.pop('dm_welcome_media_type', None)
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
        make_button(f"⚡ Approve all ({len(ids)})", callback_data=f"pend:ask:{msg.chat.id}", style=BTN_SUCCESS),
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
    done = await approve_with_progress(cb, cid, ids)
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
    maint = "ON" if is_maintenance() else "OFF"
    return InlineKeyboardMarkup(inline_keyboard=[
        [make_button("📊 Stats", callback_data="adm:stats", style=BTN_PRIMARY),
         make_button("📡 Chats", callback_data="adm:chats", style=BTN_PRIMARY)],
        [make_button("👥 Users", callback_data="adm:users", style=BTN_PRIMARY),
         make_button("📢 Force-sub", callback_data="adm:fsub", style=BTN_PRIMARY)],
        [make_button("📈 Dashboard", callback_data="adm:dash:ov", style=BTN_PRIMARY),
         make_button("🚫 Banned Users", callback_data="adm:banned", style=BTN_DANGER)],
        [make_button(f"🛠 Maintenance: {maint}", callback_data="adm:maint", style=BTN_DANGER if is_maintenance() else BTN_SUCCESS),
         make_button("📄 Export CSV", callback_data="adm:csv", style=BTN_PRIMARY)],
        [make_button("🔄 Reset verifications", callback_data="adm:resetverify", style=BTN_DANGER),
         make_button("📣 Broadcast help", callback_data="adm:bcast", style=BTN_PRIMARY)],
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
    parts = cb.data.split(':')
    action = parts[1] if len(parts) > 1 else ''
    await cb.answer()
    if action == 'analytics':
        days = _last_days(7)
        totals, total = {}, 0
        for d in days:
            for cid, n in analytics.get(d, {}).items():
                totals[cid] = totals.get(cid, 0) + n
                total += n
        lines = [f"• <code>{cid}</code> — {n}" for cid, n in sorted(totals.items(), key=lambda x: -x[1])[:10]]
        body = "\n".join(lines) if lines else "No approvals yet."
        return await cb.message.answer(
            f"📈 <b>Last 7 days</b>\nApprovals: {total}\nAll-time approvals: {all_time_approvals()}\n{body}",
            parse_mode=ParseMode.HTML)
    if action == 'dash':
        view = parts[2] if len(parts) > 2 else 'ov'
        text = dashboard_text(view)
        return await cb.message.answer(text, parse_mode=ParseMode.HTML, reply_markup=dashboard_markup())
    if action == 'banned':
        return await cb.message.answer(banned_list_text(), parse_mode=ParseMode.HTML)
    if action == 'maint':
        glob = group_settings.setdefault('_global', {})
        glob['maintenance'] = not glob.get('maintenance', False)
        save_json(SETTINGS_FN, group_settings)
        await cb.message.answer(f"🛠 Maintenance mode is now {'ON' if glob['maintenance'] else 'OFF'}.")
        return await cb.message.edit_reply_markup(reply_markup=_admin_panel_markup())
    if action == 'csv':
        return await send_users_csv(cb.message)
    if action == 'resetverify':
        n = await reset_verifications()
        return await cb.message.answer(f"🔄 Verifications reset. Cancelled {n} pending captcha(s).")
    if action == 'fsub':
        return await show_fsub_panel(cb.message)
    if action == 'fsubadd':
        pending_fsub_add.add(cb.from_user.id)
        return await cb.message.answer("➕ Send the channel as: <chat_id> <invite_url>", parse_mode=ParseMode.HTML)
    if action == 'fsubrm' and len(parts) > 2 and parts[2].lstrip('-').isdigit():
        cid = int(parts[2])
        FORCE_SUB_CHANNELS[:] = [c for c in FORCE_SUB_CHANNELS if c['id'] != cid]
        save_json(FSUB_FN, FORCE_SUB_CHANNELS)
        return await cb.message.answer(f"✅ Removed <code>{cid}</code>.", parse_mode=ParseMode.HTML)
    if action == 'bcast':
        return await cb.message.answer("📣 Reply to any message with /broadcast (or /pbroadcast to pin it) to send it to all users.")
    if action == 'stats':
        active = sum(1 for v in user_sessions.values() if v.get('is_active'))
        text = (f"📊 <b>Bot stats</b>\nUsers: {len(accepted_users)}\nChats: {len(groups)}\n"
                f"Logged-in accounts: {active}\nChats with a mode: {len(limits)}\nMonthly active users: {active_users_within(30)}")
    elif action == 'chats':
        text = "📡 Chats: " + (str(len(groups)) if groups else "none") + "\n" + "\n".join(f"• {h(str(t))} — <code>{c}</code>" for c, t in list(groups.items())[:30])
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
    return InlineKeyboardMarkup(inline_keyboard=[[
        make_button("« BACK", callback_data="help:back", style=BTN_PRIMARY),
        make_button("✕ CLOSE", callback_data="help:close", style=BTN_DANGER),
    ]])

def privacy_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        make_button("« BACK", callback_data="help:back", style=BTN_PRIMARY),
        make_button("✕ CLOSE", callback_data="help:close", style=BTN_DANGER),
    ]])

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
    await msg.answer(PRIVACY_TEXT_SHORT, parse_mode=ParseMode.HTML, reply_markup=privacy_keyboard())


async def decline_users(chat_id: int, user_ids, cfg: dict = None) -> list:
    """Decline pending join requests: bot first, then a logged-in admin session."""
    owner = (cfg or {}).get('owner_id')
    declined = []
    session = None
    for uid in user_ids:
        try:
            clear_pending_req(chat_id, uid)
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


@dp.callback_query(lambda c: c.data in ('wel:about', 'wel:help', 'wel:settings'))
async def welcome_buttons(cb: CallbackQuery):
    if cb.data == 'wel:settings':
        await cb.message.answer(SETTINGS_TITLE, reply_markup=settings_main_markup(cb.from_user.id), parse_mode=ParseMode.HTML)
    elif cb.data == 'wel:about':
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


# ================= SPIDEY FEATURE SET 7 =================
JOIN_FN = DATA_DIR / 'join_times.json'
ANALYTICS_FN = DATA_DIR / 'analytics.json'
CAPTCHA_FN = DATA_DIR / 'captcha_pending.json'
join_times = load_json(JOIN_FN, {})          # "chat:uid" -> unix time of join
analytics = load_json(ANALYTICS_FN, {})      # "YYYY-MM-DD" -> {chat_id: approvals}
captcha_pending = load_json(CAPTCHA_FN, {})  # "chat:uid" -> {chat, uid, expires}
GROUP_SETTING_KEYS['captcha'] = 'Captcha'
GROUP_SETTING_KEYS['antispam'] = 'Anti-spam'
GROUP_SETTING_KEYS['require_username'] = 'Require username'
LOCK_LABELS = {'links': 'Links', 'stickers': 'Stickers', 'photos': 'Photos', 'videos': 'Videos', 'forwards': 'Forwards'}

def log_channel_id():
    return group_settings.get('_global', {}).get('log_channel')

async def log_event(text: str):
    cid = log_channel_id()
    if not cid or is_chan_banned(cid):
        return
    try:
        await bot.send_message(int(cid), text, parse_mode=ParseMode.HTML,
                               link_preview_options=types.LinkPreviewOptions(is_disabled=True))
    except Exception as e:
        logging.warning(f"Log channel send failed: {e}")

def count_approval(chat_id: int):
    day = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    bucket = analytics.setdefault(day, {})
    bucket[str(chat_id)] = bucket.get(str(chat_id), 0) + 1
    analytics['_total'] = analytics.get('_total', 0) + 1   # all-time counter
    save_json(ANALYTICS_FN, analytics)

def all_time_approvals() -> int:
    return int(analytics.get('_total', 0))

@dp.message(Command('setlog'), F.chat.type == ChatType.PRIVATE)
async def cmd_setlog(msg: types.Message):
    if not is_bot_admin(msg.from_user.id):
        return
    parts = (msg.text or '').split()
    glob = group_settings.setdefault('_global', {})
    if len(parts) < 2:
        return await msg.answer("Usage: /setlog &lt;channel_id&gt;  or  /setlog off", parse_mode=ParseMode.HTML)
    if parts[1].lower() == 'off':
        glob.pop('log_channel', None)
        msg_text = "✅ Activity logging turned off."
    elif parts[1].lstrip('-').isdigit():
        glob['log_channel'] = int(parts[1])
        msg_text = f"✅ Activity log channel set to <code>{parts[1]}</code>."
    else:
        return await msg.answer("❌ Give a numeric channel id.")
    save_json(SETTINGS_FN, group_settings)
    await msg.answer(msg_text, parse_mode=ParseMode.HTML)

@dp.message(Command('analytics'), F.chat.type == ChatType.PRIVATE)
async def cmd_analytics(msg: types.Message):
    if not is_bot_admin(msg.from_user.id):
        return
    today = datetime.now(timezone.utc)
    days = [(today - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7)]
    totals, total = {}, 0
    for d in days:
        for cid, n in analytics.get(d, {}).items():
            totals[cid] = totals.get(cid, 0) + n
            total += n
    lines = [f"• <code>{cid}</code> — {n}" for cid, n in sorted(totals.items(), key=lambda x: -x[1])[:10]]
    body = "\n".join(lines) if lines else "No approvals yet."
    await msg.answer(f"📈 <b>Last 7 days</b>\nApprovals: {total}\nAll-time approvals: {all_time_approvals()}\n{body}", parse_mode=ParseMode.HTML)

@dp.callback_query(lambda c: c.data == 'unj:drop')
async def unjoined_drop(cb: CallbackQuery):
    if not is_bot_admin(cb.from_user.id):
        return await cb.answer("⛔ Admins only.", show_alert=True)
    removed = 0
    for uid in list(accepted_users):
        if await missing_force_sub(uid):
            accepted_users.discard(uid)
            removed += 1
    save_state()
    await cb.answer("Done")
    await cb.message.answer(f"🧹 Removed {removed} unjoined user(s) from the broadcast list.")


# ================= ADMIN PANEL FEATURES FROM AK-YT =================
BANS_FN = DATA_DIR / 'bans.json'
FAILS_FN = DATA_DIR / 'failures.json'
SUSPECT_FN = DATA_DIR / 'suspect.json'
bans = load_json(BANS_FN, {})          # uid -> {"until": ts or None, "reason": str}
failures = load_json(FAILS_FN, {})     # "YYYY-MM-DD" -> {reason: count}
suspect = load_json(SUSPECT_FN, {})    # uid -> captcha expirations

def is_banned(uid: int) -> bool:
    info = bans.get(str(uid))
    if not info:
        return False
    if info.get('until') and time.time() >= info['until']:
        bans.pop(str(uid), None)
        save_json(BANS_FN, bans)
        return False
    return True

def is_maintenance() -> bool:
    return bool(group_settings.get('_global', {}).get('maintenance'))

def banner_url():
    return group_settings.get('_global', {}).get('banner')

def record_failure(reason: str):
    day = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    bucket = failures.setdefault(day, {})
    bucket[reason] = bucket.get(reason, 0) + 1
    save_json(FAILS_FN, failures)

def _last_days(n: int):
    today = datetime.now(timezone.utc)
    return [(today - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(n)]

def dashboard_text(view: str) -> str:
    days = _last_days(7)
    if view == 'top':
        totals = {}
        for d in days:
            for cid, n in analytics.get(d, {}).items():
                totals[cid] = totals.get(cid, 0) + n
        body = "\n".join(f"• <code>{c}</code> — {n}" for c, n in sorted(totals.items(), key=lambda x: -x[1])[:10]) or "No data."
        return f"🏆 <b>Top chats (7 days)</b>\n{body}"
    if view == 'fail':
        totals = {}
        for d in days:
            for reason, n in failures.get(d, {}).items():
                totals[reason] = totals.get(reason, 0) + n
        body = "\n".join(f"• {h(r)} — {n}" for r, n in sorted(totals.items(), key=lambda x: -x[1])) or "No failures."
        return f"❌ <b>Failure reasons (7 days)</b>\n{body}"
    if view == 'sus':
        body = "\n".join(f"• <code>{u}</code> — {n} captcha expiries" for u, n in sorted(suspect.items(), key=lambda x: -x[1]) if n >= 2) or "No suspicious users."
        return f"⚠️ <b>Suspicious users</b> (2+ captcha expiries)\n{body}"
    lines = []
    for d in reversed(days):
        total = sum(analytics.get(d, {}).values())
        lines.append(f"{d}: <b>{total}</b> approvals")
    return "📈 <b>Daily approvals (7 days)</b>\n" + "\n".join(lines)

def dashboard_markup() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [make_button("📈 Daily", callback_data="adm:dash:ov", style=BTN_PRIMARY),
         make_button("🏆 Top chats", callback_data="adm:dash:top", style=BTN_PRIMARY)],
        [make_button("❌ Failures", callback_data="adm:dash:fail", style=BTN_PRIMARY),
         make_button("⚠️ Suspicious", callback_data="adm:dash:sus", style=BTN_PRIMARY)],
    ])

def banned_list_text() -> str:
    if not bans:
        return "🚫 No banned users."
    lines = []
    for uid, info in bans.items():
        left = "permanent" if not info.get('until') else f"until {datetime.fromtimestamp(info['until'], timezone.utc).strftime('%Y-%m-%d %H:%M')} UTC"
        lines.append(f"• <code>{uid}</code> — {left}" + (f" — {h(info.get('reason', ''))}" if info.get('reason') else ""))
    return f"🚫 <b>Banned users ({len(bans)})</b>\n" + "\n".join(lines)

async def send_users_csv(message):
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(['user_id', 'accepted', 'last_seen_utc', 'banned'])
    ids = set(accepted_users) | {int(k) for k in user_last_seen.keys()}
    for uid in sorted(ids):
        seen = user_last_seen.get(str(uid))
        seen_txt = datetime.fromtimestamp(seen, timezone.utc).isoformat() if seen else ''
        writer.writerow([uid, uid in accepted_users, seen_txt, is_banned(uid)])
    data = buf.getvalue().encode('utf-8')
    await message.answer_document(BufferedInputFile(data, filename='users.csv'),
                                  caption=f"📄 {len(ids)} user(s) exported.")

async def reset_verifications() -> int:
    cancelled = 0
    for key, task in list(_captcha_tasks.items()):
        task.cancel()
        cancelled += 1
    _captcha_tasks.clear()
    captcha_pending.clear()
    join_times.clear()
    suspect.clear()
    save_json(CAPTCHA_FN, captcha_pending)
    save_json(JOIN_FN, join_times)
    save_json(SUSPECT_FN, suspect)
    return cancelled

async def _parse_target_and_rest(msg: types.Message):
    """Returns (target_user, rest_tokens). Target from reply or first argument."""
    parts = (msg.text or '').split()
    args = parts[1:]
    if msg.reply_to_message and msg.reply_to_message.from_user:
        return msg.reply_to_message.from_user, args
    if not args:
        return None, []
    return await _target_user(msg), args[1:]

@dp.message(Command('banuser'), F.chat.type == ChatType.PRIVATE)
async def cmd_banuser(msg: types.Message):
    if not is_bot_admin(msg.from_user.id):
        return
    target, rest = await _parse_target_and_rest(msg)
    if not target:
        return await msg.answer("Usage: /banuser &lt;id or @username&gt; [reason]  or reply to a user", parse_mode=ParseMode.HTML)
    bans[str(target.id)] = {'until': None, 'reason': ' '.join(rest)}
    save_json(BANS_FN, bans)
    await msg.answer(f"🚫 <code>{target.id}</code> banned permanently.", parse_mode=ParseMode.HTML)

@dp.message(Command('tempban'), F.chat.type == ChatType.PRIVATE)
async def cmd_tempban_user(msg: types.Message):
    if not is_bot_admin(msg.from_user.id):
        return
    target, rest = await _parse_target_and_rest(msg)
    seconds = parse_duration(rest[0]) if rest else None
    if not target or not seconds:
        return await msg.answer("Usage: /tempban &lt;id or @username&gt; &lt;30m|12h|7d|2w&gt; [reason]", parse_mode=ParseMode.HTML)
    bans[str(target.id)] = {'until': time.time() + seconds, 'reason': ' '.join(rest[1:])}
    save_json(BANS_FN, bans)
    await msg.answer(f"⏳ <code>{target.id}</code> banned for {rest[0]}.", parse_mode=ParseMode.HTML)

@dp.message(Command('unbanuser'), F.chat.type == ChatType.PRIVATE)
async def cmd_unbanuser(msg: types.Message):
    if not is_bot_admin(msg.from_user.id):
        return
    target, _ = await _parse_target_and_rest(msg)
    if not target:
        return await msg.answer("Usage: /unbanuser &lt;id or @username&gt;", parse_mode=ParseMode.HTML)
    bans.pop(str(target.id), None)
    save_json(BANS_FN, bans)
    await msg.answer(f"✅ <code>{target.id}</code> unbanned.", parse_mode=ParseMode.HTML)

@dp.message(Command('banned'), F.chat.type == ChatType.PRIVATE)
async def cmd_banned(msg: types.Message):
    if not is_bot_admin(msg.from_user.id):
        return
    await msg.answer(banned_list_text(), parse_mode=ParseMode.HTML)

@dp.message(Command('maintenance'), F.chat.type == ChatType.PRIVATE)
async def cmd_maintenance(msg: types.Message):
    if not is_bot_admin(msg.from_user.id):
        return
    parts = (msg.text or '').split()
    glob = group_settings.setdefault('_global', {})
    if len(parts) < 2 or parts[1].lower() not in ('on', 'off'):
        return await msg.answer(f"Maintenance is {'ON' if is_maintenance() else 'OFF'}. Usage: /maintenance on|off")
    glob['maintenance'] = parts[1].lower() == 'on'
    save_json(SETTINGS_FN, group_settings)
    await msg.answer(f"🛠 Maintenance mode {'ON' if glob['maintenance'] else 'OFF'}.")

@dp.message(Command('setbanner'), F.chat.type == ChatType.PRIVATE)
async def cmd_setbanner(msg: types.Message):
    if not is_bot_admin(msg.from_user.id):
        return
    glob = group_settings.setdefault('_global', {})
    parts = (msg.text or '').split(maxsplit=1)
    if msg.reply_to_message and msg.reply_to_message.photo:
        glob['banner'] = msg.reply_to_message.photo[-1].file_id
        text = "✅ Banner set from the replied photo."
    elif len(parts) >= 2 and parts[1].lower() == 'off':
        glob.pop('banner', None)
        text = "✅ Banner removed; random pictures are used again."
    elif len(parts) >= 2 and parts[1].startswith(('http://', 'https://')):
        glob['banner'] = parts[1].strip()
        text = "✅ Banner URL set."
    else:
        return await msg.answer("Usage: reply to a photo with /setbanner, or /setbanner &lt;image_url&gt; or /setbanner off", parse_mode=ParseMode.HTML)
    save_json(SETTINGS_FN, group_settings)
    await msg.answer(text)

@dp.message(Command('dashboard'), F.chat.type == ChatType.PRIVATE)
async def cmd_dashboard(msg: types.Message):
    if not is_bot_admin(msg.from_user.id):
        return
    await msg.answer(dashboard_text('ov'), parse_mode=ParseMode.HTML, reply_markup=dashboard_markup())

@dp.message(Command('exportcsv'), F.chat.type == ChatType.PRIVATE)
async def cmd_exportcsv(msg: types.Message):
    if not is_bot_admin(msg.from_user.id):
        return
    await send_users_csv(msg)

@dp.message(Command('resetverify'), F.chat.type == ChatType.PRIVATE)
async def cmd_resetverify(msg: types.Message):
    if not is_bot_admin(msg.from_user.id):
        return
    n = await reset_verifications()
    await msg.answer(f"🔄 Verifications reset. Cancelled {n} pending captcha(s).")


# ================= ADMIN MANAGEMENT + WEB ADMIN PANEL (from ak-ultra) =================
import hashlib, hmac, secrets, html as htmllib
WEB_ADMINS_FN = DATA_DIR / 'web_admins.json'
web_admins = load_json(WEB_ADMINS_FN, {})   # username -> {"uid": int, "salt": str, "hash": str}
WEB_SECRET = secrets.token_bytes(32)        # random per start: restarting logs web admins out
WEB_SESSION_HOURS = 12
_login_fails = {}                           # ip -> [timestamps]
_ADMIN_USER_RE = re.compile(r'^[A-Za-z0-9_]{3,20}$')

def _pw_hash(password: str, salt: str = None):
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 200_000).hex()
    return salt, digest

def _sign(value: str) -> str:
    return hmac.new(WEB_SECRET, value.encode(), hashlib.sha256).hexdigest()

def _session_user(request):
    raw = request.cookies.get('ak_sess')
    if not raw:
        return None
    parts = raw.split('.')
    if len(parts) != 3:
        return None
    username, exp, sig = parts
    if not hmac.compare_digest(_sign(f"{username}.{exp}"), sig) or int(exp) < time.time():
        return None
    return username if username in web_admins else None

def _too_many_fails(ip: str) -> bool:
    now = time.time()
    recent = [t for t in _login_fails.get(ip, []) if now - t < 600]
    _login_fails[ip] = recent
    return len(recent) >= 5

CSS_TEXT = (
    "body{font-family:system-ui,sans-serif;background:#0f1419;color:#e6e6e6;margin:0;padding:16px}"
    "h1{font-size:20px}.card{background:#1a222c;border-radius:12px;padding:14px;margin:10px 0}"
    "table{width:100%;border-collapse:collapse;font-size:14px}td,th{border-bottom:1px solid #2c3642;padding:6px;text-align:left}"
    "input,textarea{width:100%;box-sizing:border-box;background:#0f1419;color:#e6e6e6;border:1px solid #2c3642;border-radius:8px;padding:8px;margin:4px 0}"
    "button,a.btn{background:#2b7de9;color:#fff;border:0;border-radius:8px;padding:8px 14px;text-decoration:none;display:inline-block;cursor:pointer;margin:4px 4px 4px 0}"
    ".danger{background:#c0392b}nav a{margin-right:12px;color:#8ab4f8}"
)

def _page(title: str, body: str) -> str:
    return ("<!doctype html><html><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
            f"<title>{htmllib.escape(title)}</title><style>{CSS_TEXT}</style></head><body>{body}</body></html>")

NAV = ("<nav><a href=\"/admin\">Overview</a><a href=\"/admin/dashboard\">Dashboard</a><a href=\"/admin/users\">Users</a><a href=\"/admin/chats\">Chats</a>"
       "<a href=\"/admin/bans\">Bans</a><a href=\"/admin/broadcast\">Broadcast</a><a href=\"/admin/settings\">Settings</a>"
       "<a href=\"/admin/export.csv\">CSV</a><a href=\"/admin/logout\">Logout</a></nav>")

def register_admin_web(app):
    from aiohttp import web

    def html_resp(body_html: str, title: str = "AK Admin"):
        return web.Response(text=_page(title, body_html), content_type='text/html')

    def login_page(error: str = ""):
        err = f"<p style='color:#ff8080'>{htmllib.escape(error)}</p>" if error else ""
        return html_resp(
            "<h1>Admin login</h1><div class='card'>" + err +
            "<form method='post' action='/admin/login'>"
            "<input name='username' placeholder='Username' autocomplete='username' required>"
            "<input name='password' type='password' placeholder='Password' autocomplete='current-password' required>"
            "<button type='submit'>Login</button></form></div>", "Login")

    async def admin_get(request):
        if not _session_user(request):
            return login_page()
        active = sum(1 for v in user_sessions.values() if v.get('is_active'))
        today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        today_count = sum(analytics.get(today, {}).values())
        week = sum(sum(analytics.get(d, {}).values()) for d in _last_days(7))
        body = (NAV + "<h1>Overview</h1><div class='card'>"
                f"<p>Users: <b>{len(accepted_users)}</b> · Monthly active: <b>{active_users_within(30)}</b></p>"
                f"<p>Chats: <b>{len(groups)}</b> · Chats with a mode: <b>{len(limits)}</b></p>"
                f"<p>Approvals today: <b>{today_count}</b> · Last 7 days: <b>{week}</b> · All-time: <b>{all_time_approvals()}</b></p>"
                f"<p>Banned users: <b>{len(bans)}</b> · Logged-in accounts: <b>{active}</b></p>"
                f"<p>Maintenance: <b>{'ON' if is_maintenance() else 'OFF'}</b></p>"
                f"<p>Python: <b>{python_info()}</b></p></div>")
        return html_resp(body, "Overview")

    async def login_post(request):
        ip = request.remote or 'unknown'
        if _too_many_fails(ip):
            return html_resp("<p>Too many failed attempts. Try again in 10 minutes.</p>", "Locked")
        data = await request.post()
        username = str(data.get('username', '')).strip()
        password = str(data.get('password', ''))
        rec = web_admins.get(username)
        ok = False
        if rec:
            _, digest = _pw_hash(password, rec['salt'])
            ok = hmac.compare_digest(digest, rec['hash'])
        if not ok:
            _login_fails.setdefault(ip, []).append(time.time())
            return login_page("Wrong username or password.")
        exp = int(time.time() + WEB_SESSION_HOURS * 3600)
        val = f"{username}.{exp}"
        resp = web.HTTPFound('/admin')
        resp.set_cookie('ak_sess', f"{val}.{_sign(val)}", httponly=True, secure=True,
                        samesite='Strict', max_age=WEB_SESSION_HOURS * 3600)
        return resp

    async def logout(request):
        resp = web.HTTPFound('/admin')
        resp.del_cookie('ak_sess')
        return resp

    def guard(handler):
        async def wrapped(request):
            if not _session_user(request):
                return login_page()
            return await handler(request)
        return wrapped

    async def dashboard_page(request):
        days = _last_days(7)
        daily = "".join(f"<tr><td>{d}</td><td>{sum(analytics.get(d, {}).values())}</td></tr>" for d in reversed(days))
        totals = {}
        for d in days:
            for cid, n in analytics.get(d, {}).items():
                totals[cid] = totals.get(cid, 0) + n
        top = "".join(
            f"<tr><td><code>{cid}</code></td><td>{htmllib.escape(str(groups.get(cid, '')))}</td><td>{n}</td></tr>"
            for cid, n in sorted(totals.items(), key=lambda x: -x[1])[:10])
        fails = {}
        for d in days:
            for reason, n in failures.get(d, {}).items():
                fails[reason] = fails.get(reason, 0) + n
        fail_rows = "".join(f"<tr><td>{htmllib.escape(r)}</td><td>{n}</td></tr>" for r, n in sorted(fails.items(), key=lambda x: -x[1]))
        sus_rows = "".join(
            f"<tr><td><code>{u}</code></td><td>{n}</td><td><form method='post' action='/admin/ban'>"
            f"<input type='hidden' name='uid' value='{u}'><input type='hidden' name='reason' value='suspicious captcha'>"
            f"<button class='danger'>Ban</button></form></td></tr>"
            for u, n in sorted(suspect.items(), key=lambda x: -x[1]) if n >= 2)
        return html_resp(NAV + "<h1>Dashboard</h1>"
            "<div class='card'><h3>Daily approvals (7 days)</h3><table><tr><th>Date (UTC)</th><th>Approvals</th></tr>" + daily + "</table></div>"
            "<div class='card'><h3>Top chats (7 days)</h3><table><tr><th>ID</th><th>Name</th><th>Approvals</th></tr>" + (top or "<tr><td colspan=3>No data</td></tr>") + "</table></div>"
            "<div class='card'><h3>Failure reasons (7 days)</h3><table><tr><th>Reason</th><th>Count</th></tr>" + (fail_rows or "<tr><td colspan=2>No failures</td></tr>") + "</table></div>"
            "<div class='card'><h3>Suspicious users (2+ captcha expiries)</h3><table><tr><th>User</th><th>Expiries</th><th></th></tr>" + (sus_rows or "<tr><td colspan=3>None</td></tr>") + "</table></div>",
            "Dashboard")

    async def users_page(request):
        rows = []
        ids = sorted(set(accepted_users) | {int(k) for k in user_last_seen.keys()})[:500]
        for uid in ids:
            seen = user_last_seen.get(str(uid))
            seen_txt = datetime.fromtimestamp(seen, timezone.utc).strftime('%Y-%m-%d %H:%M') if seen else '-'
            rows.append(f"<tr><td><code>{uid}</code></td><td>{'yes' if uid in accepted_users else 'no'}</td>"
                        f"<td>{seen_txt}</td><td>{'banned' if is_banned(uid) else ''}</td></tr>")
        return html_resp(NAV + "<h1>Users</h1><div class='card'><table><tr><th>ID</th><th>Accepted</th><th>Last seen (UTC)</th><th>Status</th></tr>"
                         + "".join(rows) + "</table></div>", "Users")

    async def chats_page(request):
        rows = []
        for cid, title in list(groups.items())[:500]:
            cfg = limits.get(str(cid), {})
            rows.append(f"<tr><td>{htmllib.escape(str(title))}</td><td><code>{cid}</code></td>"
                        f"<td>{cfg.get('mode', '-')}</td><td>{'on' if chat_setting(int(cid), 'autoapprove') else 'off'}</td></tr>")
        return html_resp(NAV + "<h1>Chats</h1><div class='card'><table><tr><th>Name</th><th>ID</th><th>Mode</th><th>Auto-approve</th></tr>"
                         + "".join(rows) + "</table></div>", "Chats")

    async def bans_page(request):
        return html_resp(NAV + "<h1>Bans</h1><div class='card'>"
                         "<form method='post' action='/admin/ban'>"
                         "<input name='uid' placeholder='User ID' required>"
                         "<input name='days' placeholder='Days (empty = permanent)'>"
                         "<input name='reason' placeholder='Reason (optional)'>"
                         "<button type='submit' class='danger'>Ban</button></form></div>"
                         "<div class='card'><table><tr><th>User</th><th>Until</th><th>Reason</th><th></th></tr>"
                         + "".join(
                             f"<tr><td><code>{uid}</code></td><td>{'permanent' if not info.get('until') else datetime.fromtimestamp(info['until'], timezone.utc).strftime('%Y-%m-%d %H:%M')}</td>"
                             f"<td>{htmllib.escape(info.get('reason', ''))}</td>"
                             f"<td><form method='post' action='/admin/unban'><input type='hidden' name='uid' value='{uid}'><button>Unban</button></form></td></tr>"
                             for uid, info in bans.items())
                         + "</table></div>", "Bans")

    async def ban_post(request):
        data = await request.post()
        uid = str(data.get('uid', '')).strip()
        if not uid.lstrip('-').isdigit():
            return html_resp("<p>Invalid user id.</p>", "Error")
        days = str(data.get('days', '')).strip()
        until = time.time() + int(days) * 86400 if days.isdigit() else None
        bans[uid] = {'until': until, 'reason': str(data.get('reason', ''))[:200]}
        save_json(BANS_FN, bans)
        raise web.HTTPFound('/admin/bans')

    async def unban_post(request):
        data = await request.post()
        bans.pop(str(data.get('uid', '')).strip(), None)
        save_json(BANS_FN, bans)
        raise web.HTTPFound('/admin/bans')

    async def broadcast_page(request):
        return html_resp(NAV + "<h1>Broadcast</h1><div class='card'><form method='post' action='/admin/broadcast'>"
                         "<textarea name='text' rows='6' placeholder='Message to all users (plain text)' required></textarea>"
                         "<button type='submit'>Send to all users</button></form></div>", "Broadcast")

    async def broadcast_post(request):
        data = await request.post()
        text = str(data.get('text', '')).strip()
        if not text:
            return html_resp("<p>Empty message.</p>", "Error")

        async def run():
            ok = fail = 0
            for uid in list(accepted_users):
                try:
                    await bot.send_message(uid, text, parse_mode=None)
                    ok += 1
                except Exception:
                    fail += 1
                await asyncio.sleep(0.05)
            logging.info(f"Web broadcast done: sent {ok}, failed {fail}")
        task = asyncio.create_task(run())
        _background_tasks.add(task)
        task.add_done_callback(_background_tasks.discard)
        return html_resp(NAV + f"<div class='card'><p>Broadcast started to {len(accepted_users)} user(s). Results are in the logs.</p></div>", "Broadcast")

    async def settings_page(request):
        fsub = "".join(f"<li><code>{c['id']}</code> — {htmllib.escape(c['url'])}</li>" for c in FORCE_SUB_CHANNELS) or "<li>none</li>"
        banner = htmllib.escape(banner_url() or 'default pictures')
        return html_resp(NAV + "<h1>Settings</h1>"
                         f"<div class='card'><p>Maintenance: <b>{'ON' if is_maintenance() else 'OFF'}</b></p>"
                         "<form method='post' action='/admin/maintenance'><button type='submit'>Toggle maintenance</button></form></div>"
                         f"<div class='card'><p>Banner: {banner}</p><form method='post' action='/admin/banner'>"
                         "<input name='url' placeholder='Image URL (empty = reset)'><button type='submit'>Save banner</button></form></div>"
                         f"<div class='card'><h3>Force-sub channels</h3><ul>{fsub}</ul>"
                         "<form method='post' action='/admin/fsub'><input name='chat_id' placeholder='Channel ID' required>"
                         "<input name='url' placeholder='Invite URL (empty = remove)'><button type='submit'>Save</button></form></div>",
                         "Settings")

    async def maintenance_post(request):
        glob = group_settings.setdefault('_global', {})
        glob['maintenance'] = not glob.get('maintenance', False)
        save_json(SETTINGS_FN, group_settings)
        raise web.HTTPFound('/admin/settings')

    async def banner_post(request):
        data = await request.post()
        url = str(data.get('url', '')).strip()
        glob = group_settings.setdefault('_global', {})
        if url.startswith(('http://', 'https://')):
            glob['banner'] = url
        else:
            glob.pop('banner', None)
        save_json(SETTINGS_FN, group_settings)
        raise web.HTTPFound('/admin/settings')

    async def fsub_post(request):
        data = await request.post()
        cid_s = str(data.get('chat_id', '')).strip()
        url = str(data.get('url', '')).strip()
        if cid_s.lstrip('-').isdigit():
            cid = int(cid_s)
            FORCE_SUB_CHANNELS[:] = [c for c in FORCE_SUB_CHANNELS if c['id'] != cid]
            if url.startswith(('http://', 'https://', 'tg://')):
                FORCE_SUB_CHANNELS.append({'id': cid, 'url': url})
            save_json(FSUB_FN, FORCE_SUB_CHANNELS)
        raise web.HTTPFound('/admin/settings')

    async def csv_get(request):
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(['user_id', 'accepted', 'last_seen_utc', 'banned'])
        for uid in sorted(set(accepted_users) | {int(k) for k in user_last_seen.keys()}):
            seen = user_last_seen.get(str(uid))
            writer.writerow([uid, uid in accepted_users,
                             datetime.fromtimestamp(seen, timezone.utc).isoformat() if seen else '', is_banned(uid)])
        return web.Response(body=buf.getvalue().encode('utf-8'), content_type='text/csv',
                            headers={'Content-Disposition': 'attachment; filename="users.csv"'})

    async def channels_csv_get(request):
        return web.Response(body=channels_csv_bytes(), content_type='text/csv',
                            headers={'Content-Disposition': 'attachment; filename="channels.csv"'})

    app.router.add_get('/admin', admin_get)
    app.router.add_post('/admin/login', login_post)
    app.router.add_get('/admin/logout', logout)
    app.router.add_get('/admin/users', guard(users_page))
    app.router.add_get('/admin/dashboard', guard(dashboard_page))
    app.router.add_get('/admin/chats', guard(chats_page))
    app.router.add_get('/admin/bans', guard(bans_page))
    app.router.add_post('/admin/ban', guard(ban_post))
    app.router.add_post('/admin/unban', guard(unban_post))
    app.router.add_get('/admin/broadcast', guard(broadcast_page))
    app.router.add_post('/admin/broadcast', guard(broadcast_post))
    app.router.add_get('/admin/settings', guard(settings_page))
    app.router.add_post('/admin/maintenance', guard(maintenance_post))
    app.router.add_post('/admin/banner', guard(banner_post))
    app.router.add_post('/admin/fsub', guard(fsub_post))
    app.router.add_get('/admin/export.csv', guard(csv_get))
    app.router.add_get('/admin/export/channels.csv', guard(channels_csv_get))

# ---------- Owner commands: manage web admins ----------
def _owner_only(msg: types.Message) -> bool:
    return msg.from_user.id == OWNER_ID

@dp.message(Command('makeadmin'), F.chat.type == ChatType.PRIVATE)
async def cmd_makeadmin(msg: types.Message):
    if not _owner_only(msg):
        return
    parts = (msg.text or '').split()
    if len(parts) < 4 or not parts[1].lstrip('-').isdigit():
        return await msg.answer("Usage: /makeadmin &lt;user_id&gt; &lt;username&gt; &lt;password&gt;\n"
                                "Username: 3-20 letters/digits/_. Password: at least 8 characters.",
                                parse_mode=ParseMode.HTML)
    uid, username, password = int(parts[1]), parts[2], parts[3]
    try:
        await msg.delete()   # the command contains the password
    except Exception:
        pass
    if not _ADMIN_USER_RE.match(username):
        return await msg.answer("❌ Username must be 3-20 letters, digits or _.")
    if len(password) < 8:
        return await msg.answer("❌ Password must be at least 8 characters.")
    if username in web_admins and web_admins[username].get('uid') != uid:
        return await msg.answer("❌ That username already belongs to another admin.")
    salt, digest = _pw_hash(password)
    web_admins[username] = {'uid': uid, 'salt': salt, 'hash': digest}
    save_json(WEB_ADMINS_FN, web_admins)
    await msg.answer(f"✅ Web admin <code>{htmllib.escape(username)}</code> created for <code>{uid}</code>.\n"
                     "Open the admin panel at your site's /admin page and log in.", parse_mode=ParseMode.HTML)
    try:
        await bot.send_message(uid, f"🎉 Admin access granted.\nUsername: {username}\nPassword: {password}\n"
                                    "Log in at your site's /admin page and change nothing here; keep this private.",
                               parse_mode=None)
    except Exception:
        await msg.answer("⚠️ Could not DM the new admin (they must /start the bot first). Share credentials privately.")

@dp.message(Command('removeadmin'), F.chat.type == ChatType.PRIVATE)
async def cmd_removeadmin(msg: types.Message):
    if not _owner_only(msg):
        return
    parts = (msg.text or '').split()
    if len(parts) < 2:
        return await msg.answer("Usage: /removeadmin &lt;username or user_id&gt;", parse_mode=ParseMode.HTML)
    key = parts[1]
    removed = [u for u, rec in list(web_admins.items()) if u == key or str(rec.get('uid')) == key]
    for u in removed:
        web_admins.pop(u, None)
    save_json(WEB_ADMINS_FN, web_admins)
    await msg.answer(f"✅ Removed {len(removed)} web admin(s)." if removed else "No matching web admin.")

@dp.message(Command('listadmins'), F.chat.type == ChatType.PRIVATE)
async def cmd_listadmins(msg: types.Message):
    if not _owner_only(msg):
        return
    if not web_admins:
        return await msg.answer("No web admins yet. Create one with /makeadmin.")
    lines = "\n".join(f"• <code>{htmllib.escape(u)}</code> — <code>{rec.get('uid')}</code>" for u, rec in web_admins.items())
    await msg.answer(f"👑 Web admins:\n{lines}", parse_mode=ParseMode.HTML)


# ================= FORCE-SUB LIKE AK-ULTRA =================
# Shows every channel with its title, a join button (📢) or a checkmark (✅) and the progress.
# A middleware blocks every private command and button until the user joined all channels
# (bot admins are exempt, and errors fail open so a transient API problem never locks users out).
pending_fsub_add = set()   # admin user ids waiting to send "<chat_id> <invite_url>"

async def build_fsub_gate(user):
    missing = await missing_force_sub(user.id)
    missing_ids = {c['id'] for c in missing}
    rows, total, joined = [], 0, 0
    for ch in FORCE_SUB_CHANNELS:
        try:
            chat = await bot.get_chat(ch['id'])
        except Exception as e:
            logging.warning(f"Force-sub: cannot read channel {ch['id']}: {e}")
            continue
        total += 1
        title = chat.title or 'Channel'
        link = None
        try:
            link = await bot.export_chat_invite_link(ch['id'])
        except Exception:
            pass
        link = link or ch.get('url') or (f"https://t.me/{chat.username}" if chat.username else None)
        if not link:
            total -= 1
            continue
        if ch['id'] in missing_ids:
            rows.append([make_button(f"📢 Join {title}", url=link, style=BTN_PRIMARY)])
        else:
            joined += 1
            rows.append([make_button(f"✅ {title}", url=link, style=BTN_SUCCESS)])
    rows.append([make_button("🔄 Check again", callback_data="fsub_check", style=BTN_PRIMARY)])
    remaining = total - joined
    text = (
        f"👋 Hello <b>{h(user.first_name or 'there')}</b>!\n\n"
        "⚠️ <b>Force subscribe required</b>\n\n"
        "To use this bot you must join <b>all</b> the channels below.\n\n"
        f"📊 Progress: <b>{joined}/{total}</b> joined\n"
        f"📢 Remaining: <b>{remaining}</b> channel(s)\n\n"
        "✅ = joined | 📢 = not joined\n\n"
        "Join all channels, then tap <b>Check again</b>."
    )
    return text, InlineKeyboardMarkup(inline_keyboard=rows)

class ForceSubGate(BaseMiddleware):
    async def __call__(self, handler, event, data):
        if not FORCE_SUB_CHANNELS:
            return await handler(event, data)
        if isinstance(event, types.Message):
            user = event.from_user
            if not user or event.chat.type != ChatType.PRIVATE or is_bot_admin(user.id):
                return await handler(event, data)
            if not (event.text or '').startswith('/'):
                return await handler(event, data)
            try:
                missing = await missing_force_sub(user.id)
            except Exception as e:
                logging.error(f"Force-sub gate error for {user.id}: {e}")
                return await handler(event, data)
            if not missing:
                return await handler(event, data)
            text, kb = await build_fsub_gate(user)
            try:
                await event.answer(text, reply_markup=kb, parse_mode=ParseMode.HTML)
            except Exception as e:
                logging.error(f"Could not send force-sub gate to {user.id}: {e}")
            return None
        if isinstance(event, CallbackQuery):
            user = event.from_user
            if not user or event.data == 'fsub_check' or is_bot_admin(user.id):
                return await handler(event, data)
            if not event.message or event.message.chat.type != ChatType.PRIVATE:
                return await handler(event, data)
            try:
                missing = await missing_force_sub(user.id)
            except Exception as e:
                logging.error(f"Force-sub callback gate error for {user.id}: {e}")
                return await handler(event, data)
            if not missing:
                return await handler(event, data)
            await event.answer("❌ Join all channels first.", show_alert=True)
            text, kb = await build_fsub_gate(user)
            try:
                await bot.send_message(user.id, text, reply_markup=kb, parse_mode=ParseMode.HTML)
            except Exception as e:
                logging.error(f"Could not send callback force-sub gate to {user.id}: {e}")
            return None
        return await handler(event, data)

dp.message.middleware(ForceSubGate())
dp.callback_query.middleware(ForceSubGate())

async def show_fsub_panel(message):
    rows = []
    for ch in FORCE_SUB_CHANNELS:
        try:
            title = (await bot.get_chat(ch['id'])).title or str(ch['id'])
        except Exception:
            title = str(ch['id'])
        rows.append([make_button(f"➖ Remove {title[:30]}", callback_data=f"adm:fsubrm:{ch['id']}", style=BTN_DANGER)])
    rows.append([make_button("➕ Add channel", callback_data="adm:fsubadd", style=BTN_SUCCESS)])
    rows.append([make_button("🔙 Back", callback_data="adm:stats", style=BTN_PRIMARY)])
    body = "\n".join(f"• <code>{c['id']}</code> — {h(c['url'])}" for c in FORCE_SUB_CHANNELS) or "No channels set."
    await message.answer(f"📢 <b>Force-subscribe channels ({len(FORCE_SUB_CHANNELS)})</b>\n{body}",
                         reply_markup=InlineKeyboardMarkup(inline_keyboard=rows), parse_mode=ParseMode.HTML)

@dp.message(F.chat.type == ChatType.PRIVATE, F.text, lambda m: bool(m.from_user) and m.from_user.id in pending_fsub_add)
async def fsub_add_text(msg: types.Message):
    pending_fsub_add.discard(msg.from_user.id)
    parts = msg.text.split()
    if len(parts) < 2 or not parts[0].lstrip('-').isdigit() or not parts[1].startswith(('https://', 'http://', 'tg://')):
        return await msg.answer("❌ Send: <chat_id> <invite_url>", parse_mode=ParseMode.HTML)
    cid = int(parts[0])
    FORCE_SUB_CHANNELS[:] = [c for c in FORCE_SUB_CHANNELS if c['id'] != cid] + [{'id': cid, 'url': parts[1]}]
    save_json(FSUB_FN, FORCE_SUB_CHANNELS)
    await msg.answer(f"✅ Channel <code>{cid}</code> added.", parse_mode=ParseMode.HTML)


# ================= /settings (ak-ultra style menu) =================
def settings_main_markup(uid: int) -> InlineKeyboardMarkup:
    rows = [
        [make_button("👥 My groups", callback_data="settings#groups", style=BTN_PRIMARY),
         make_button("🔔 Leave alerts", callback_data="settings#notify", style=BTN_PRIMARY)],
        [make_button("💬 DM welcome", callback_data="settings#dm", style=BTN_PRIMARY),
         make_button("🔐 Account", callback_data="settings#account", style=BTN_PRIMARY)],
    ]
    if is_bot_admin(uid):
        rows.append([make_button("🛠 Admin tools", callback_data="settings#admin", style=BTN_SUCCESS)])
    rows.append([make_button("📖 Help", callback_data="settings#help", style=BTN_PRIMARY),
                 make_button("✕ Close", callback_data="settings#close", style=BTN_DANGER)])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def settings_back_markup() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[make_button("↩ Back", callback_data="settings#main", style=BTN_DANGER)]])

SETTINGS_TITLE = "⚙️ <b>Settings</b>\nChange your settings as you wish."

@dp.message(Command('settings'), F.chat.type == ChatType.PRIVATE)
async def cmd_settings(msg: types.Message):
    await msg.answer(SETTINGS_TITLE, reply_markup=settings_main_markup(msg.from_user.id), parse_mode=ParseMode.HTML)

@dp.callback_query(lambda c: bool(c.data) and c.data.startswith('settings#'))
async def settings_callback(cb: CallbackQuery):
    uid = cb.from_user.id
    action = cb.data.split('#', 1)[1]
    try:
        await cb.answer()   # the redirect path calls this handler again; ignore "already answered"
    except Exception:
        pass
    msg = cb.message

    if action == 'main':
        return await msg.edit_text(SETTINGS_TITLE, reply_markup=settings_main_markup(uid), parse_mode=ParseMode.HTML)
    if action == 'close':
        try:
            return await msg.delete()
        except Exception:
            return
    if action == 'groups':
        gs = await _admin_groups(uid)
        if not gs:
            text = "👥 You are not an admin of any registered group yet. Add the bot to a group first."
            rows = []
        else:
            text = "👥 <b>Select a group to manage:</b>"
            rows = [[make_button(title[:40], callback_data=f"grp:open:{cid}", style=BTN_PRIMARY)] for cid, title in gs]
        rows.append([make_button("↩ Back", callback_data="settings#main", style=BTN_DANGER)])
        return await msg.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=rows), parse_mode=ParseMode.HTML)
    if action == 'notify':
        on = uid in leave_noti_users
        text = (f"🔔 <b>Leave alerts</b>\nStatus: <b>{'ON' if on else 'OFF'}</b>\n\n"
                "When ON, you get a DM whenever a member leaves a group where you are admin.")
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [make_button("Turn OFF" if on else "Turn ON", callback_data="settings#notify_toggle",
                         style=BTN_DANGER if on else BTN_SUCCESS)],
            [make_button("↩ Back", callback_data="settings#main", style=BTN_DANGER)]])
        return await msg.edit_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)
    if action == 'notify_toggle':
        if uid in leave_noti_users:
            leave_noti_users.discard(uid)
        else:
            leave_noti_users.add(uid)
        save_json(LEAVE_NOTI_FN, list(leave_noti_users))
        return await settings_callback_redirect(cb, 'notify')
    if action == 'dm':
        text = ("💬 <b>DM welcome</b>\nSent to users whose join request is approved.\n\n"
                "Set the text in a group with <code>/setdmwelcome &lt;text&gt;</code> "
                "(placeholders: {mention} {first} {chat}).\n"
                "Buttons: <code>/setwelcomebuttons</code> with lines like <code>Text | https://link | success</code>.")
        return await msg.edit_text(text, reply_markup=settings_back_markup(), parse_mode=ParseMode.HTML)
    if action == 'account':
        sess = user_sessions.get(str(uid), {})
        logged = bool(sess.get('is_active'))
        text = ("🔐 <b>Account</b>\n"
                f"Login status: <b>{'logged in' if logged else 'not logged in'}</b>\n\n"
                "Use <code>/login</code> to store your session (needed for bulk approve and /pending). "
                "Use <code>/logout</code> to remove it.")
        return await msg.edit_text(text, reply_markup=settings_back_markup(), parse_mode=ParseMode.HTML)
    if action == 'admin':
        if not is_bot_admin(uid):
            return
        return await msg.edit_text("🛠 <b>Admin tools</b>\nTap a tool.", reply_markup=admin_tools_markup(),
                                   parse_mode=ParseMode.HTML)
    if action == 'maint':
        if not is_bot_admin(uid):
            return
        glob = group_settings.setdefault('_global', {})
        glob['maintenance'] = not glob.get('maintenance', False)
        save_json(SETTINGS_FN, group_settings)
        return await msg.edit_text("🛠 <b>Admin tools</b>\nTap a tool.", reply_markup=admin_tools_markup(),
                                   parse_mode=ParseMode.HTML)
    if action == 'adminhelp':
        glob = group_settings.get('_global', {})
        log_id = glob.get('log_channel')
        banner = glob.get('banner')
        text = (f"📝 <b>Log channel:</b> {'<code>' + str(log_id) + '</code>' if log_id else 'OFF'}\n"
                "Set with <code>/setlog &lt;channel_id&gt;</code>.\n\n"
                f"🖼 <b>Banner:</b> {'custom' if banner else 'default pictures'}\n"
                "Set with a photo reply to <code>/setbanner</code>, or <code>/setbanner &lt;image_url&gt;</code>.\n\n"
                "🚫 <b>Bans:</b> <code>/banuser</code> · <code>/tempban &lt;id&gt; 7d</code> · <code>/unbanuser</code>")
        rows = []
        if log_id:
            rows.append([make_button("📝 Log channel: ON (tap to turn OFF)", callback_data="settings#logoff", style=BTN_DANGER)])
        if banner:
            rows.append([make_button("🖼 Banner: custom (tap to use default)", callback_data="settings#banneroff", style=BTN_DANGER)])
        rows.append([make_button("↩ Back", callback_data="settings#admin", style=BTN_DANGER)])
        return await msg.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=rows), parse_mode=ParseMode.HTML)
    if action in ('logoff', 'banneroff'):
        if not is_bot_admin(uid):
            return
        glob = group_settings.setdefault('_global', {})
        glob.pop('log_channel' if action == 'logoff' else 'banner', None)
        save_json(SETTINGS_FN, group_settings)
        return await settings_callback_redirect(cb, 'adminhelp')
    if action == 'help':
        return await msg.edit_text("📖 Use /cmds for the full command list, or /about for bot info.",
                                   reply_markup=settings_back_markup(), parse_mode=ParseMode.HTML)

def admin_tools_markup() -> InlineKeyboardMarkup:
    maint = "ON" if is_maintenance() else "OFF"
    return InlineKeyboardMarkup(inline_keyboard=[
        [make_button("📊 Panel", callback_data="adm:stats", style=BTN_PRIMARY),
         make_button("📈 Dashboard", callback_data="adm:dash:ov", style=BTN_PRIMARY)],
        [make_button("📅 Analytics", callback_data="adm:analytics", style=BTN_PRIMARY),
         make_button("👥 Users", callback_data="adm:users", style=BTN_PRIMARY)],
        [make_button("📄 Export CSV", callback_data="adm:csv", style=BTN_PRIMARY),
         make_button(f"🛠 Maintenance: {maint}", callback_data="settings#maint",
                     style=BTN_DANGER if is_maintenance() else BTN_SUCCESS)],
        [make_button("🚫 Banned users", callback_data="adm:banned", style=BTN_DANGER),
         make_button("📢 Force-sub", callback_data="adm:fsub", style=BTN_PRIMARY)],
        [make_button("📝 Log & banner", callback_data="settings#adminhelp", style=BTN_PRIMARY)],
        [make_button("↩ Back", callback_data="settings#main", style=BTN_DANGER)],
    ])

async def settings_callback_redirect(cb: CallbackQuery, action: str):
    """Re-render a settings sub-page after a toggle."""
    cb.data = f"settings#{action}"
    return await settings_callback(cb)


# ================= AUTO-REJECT SETTING + SCHEDULED AUTO-POST =================
GROUP_SETTING_KEYS['autoreject'] = 'Auto-reject'
AUTOPOST_FN = DATA_DIR / 'autoposts.json'
autoposts = load_json(AUTOPOST_FN, [])   # [{id, from_chat, msg_id, target, interval_hours, last_sent}]

AUTOPOST_USAGE = ("Usage:\n"
                  "Reply to a message with /autopost add &lt;hours&gt; &lt;channels|users|chat_id&gt;\n"
                  "/autopost list\n/autopost del &lt;id&gt;")

@dp.message(Command('autopost'), F.chat.type == ChatType.PRIVATE)
async def cmd_autopost(msg: types.Message):
    if not is_bot_admin(msg.from_user.id):
        return
    parts = (msg.text or '').split()
    sub = parts[1].lower() if len(parts) > 1 else ''
    if sub == 'add':
        if not msg.reply_to_message:
            return await msg.answer("❌ Reply to the message you want to schedule, then send the command.\n\n" + AUTOPOST_USAGE)
        if len(parts) < 4 or not parts[2].isdigit() or int(parts[2]) < 1:
            return await msg.answer(AUTOPOST_USAGE)
        target = parts[3].lower()
        if target not in ('channels', 'users') and not target.lstrip('-').isdigit():
            return await msg.answer(AUTOPOST_USAGE)
        pid = max((p['id'] for p in autoposts), default=0) + 1
        autoposts.append({'id': pid, 'from_chat': msg.chat.id, 'msg_id': msg.reply_to_message.message_id,
                          'target': target, 'interval_hours': int(parts[2]), 'last_sent': 0})
        save_json(AUTOPOST_FN, autoposts)
        return await msg.answer(f"✅ Auto-post #{pid} added: every {parts[2]} h to {h(target)}.")
    if sub == 'list':
        if not autoposts:
            return await msg.answer("No auto-posts scheduled.")
        lines = "\n".join(f"#{p['id']} — every {p['interval_hours']} h → {h(str(p['target']))}" for p in autoposts)
        rows = []
        for p in autoposts:
            label = 'resume' if p.get('paused') else 'pause'
            rows.append([make_button(f"#{p['id']} {label}", callback_data=f"ap:tog:{p['id']}", style=BTN_PRIMARY),
                         make_button(f"#{p['id']} delete", callback_data=f"ap:del:{p['id']}", style=BTN_DANGER)])
        return await msg.answer(f"📅 Auto-posts:\n{lines}", reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))
    if sub == 'del' and len(parts) >= 3 and parts[2].isdigit():
        before = len(autoposts)
        autoposts[:] = [p for p in autoposts if p['id'] != int(parts[2])]
        save_json(AUTOPOST_FN, autoposts)
        return await msg.answer("✅ Deleted." if len(autoposts) < before else "No auto-post with that id.")
    await msg.answer(AUTOPOST_USAGE)

async def autopost_loop():
    """Checks every minute and copies each due post to its targets."""
    while True:
        try:
            now = time.time()
            changed = False
            for post in autoposts:
                if post.get('paused') or now - post.get('last_sent', 0) < post['interval_hours'] * 3600:
                    continue
                target = post['target']
                if target == 'channels':
                    targets = [int(c) for c in groups.keys()]
                elif target == 'users':
                    targets = list(accepted_users)
                else:
                    targets = [int(target)]
                for tid in targets:
                    if is_chan_banned(tid):
                        continue  # banned chats never receive anything from the bot
                    try:
                        await bot.copy_message(chat_id=tid, from_chat_id=post['from_chat'], message_id=post['msg_id'])
                    except Exception as e:
                        logging.warning(f"Auto-post #{post['id']} to {tid} failed: {e}")
                    if target == 'users':
                        await asyncio.sleep(0.05)
                post['last_sent'] = now
                changed = True
            if changed:
                save_json(AUTOPOST_FN, autoposts)
        except Exception as e:
            logging.warning(f"Auto-post loop error: {e}")
        await asyncio.sleep(60)


# ================= REQUEST-BASED FORCE-SUB, CHANNEL BAN, BROADCAST BUTTONS =================
PENDING_REQ_FN = DATA_DIR / 'pending_requests.json'
CHAN_BANS_FN = DATA_DIR / 'channel_bans.json'
pending_reqs = load_json(PENDING_REQ_FN, {})   # "chat:uid" -> unix time
chan_bans = load_json(CHAN_BANS_FN, {})        # str(chat_id) -> reason

def has_pending_req(chat_id: int, uid: int) -> bool:
    return f"{chat_id}:{uid}" in pending_reqs

def set_pending_req(chat_id: int, uid: int):
    pending_reqs[f"{chat_id}:{uid}"] = time.time()
    save_json(PENDING_REQ_FN, pending_reqs)

def clear_pending_req(chat_id: int, uid: int):
    if pending_reqs.pop(f"{chat_id}:{uid}", None) is not None:
        save_json(PENDING_REQ_FN, pending_reqs)

def is_chan_banned(chat_id) -> bool:
    return str(chat_id) in chan_bans

class ChannelBanGate(BaseMiddleware):
    """Bot ignores everything that comes from a banned channel or group."""
    async def __call__(self, handler, event, data):
        chat = None
        if isinstance(event, types.Message):
            chat = event.chat
        elif isinstance(event, CallbackQuery) and event.message:
            chat = event.message.chat
        if chat and is_chan_banned(chat.id):
            return None
        return await handler(event, data)

dp.message.middleware(ChannelBanGate())
dp.callback_query.middleware(ChannelBanGate())

@dp.message(Command('chanban'), F.chat.type == ChatType.PRIVATE)
async def cmd_chanban(msg: types.Message):
    if not is_bot_admin(msg.from_user.id):
        return
    parts = (msg.text or '').split(maxsplit=2)
    if len(parts) < 2 or not parts[1].lstrip('-').isdigit():
        return await msg.answer("Usage: /chanban &lt;chat_id&gt; [reason]", parse_mode=ParseMode.HTML)
    chan_bans[parts[1]] = parts[2] if len(parts) > 2 else ''
    save_json(CHAN_BANS_FN, chan_bans)
    await msg.answer(f"⛔ Chat <code>{parts[1]}</code> banned. The bot will ignore it.", parse_mode=ParseMode.HTML)

@dp.message(Command('chanunban'), F.chat.type == ChatType.PRIVATE)
async def cmd_chanunban(msg: types.Message):
    if not is_bot_admin(msg.from_user.id):
        return
    parts = (msg.text or '').split()
    if len(parts) < 2:
        return await msg.answer("Usage: /chanunban &lt;chat_id&gt;", parse_mode=ParseMode.HTML)
    chan_bans.pop(parts[1], None)
    save_json(CHAN_BANS_FN, chan_bans)
    await msg.answer(f"✅ Chat <code>{parts[1]}</code> unbanned.", parse_mode=ParseMode.HTML)

@dp.message(Command('chanbanned'), F.chat.type == ChatType.PRIVATE)
async def cmd_chanbanned(msg: types.Message):
    if not is_bot_admin(msg.from_user.id):
        return
    if not chan_bans:
        return await msg.answer("No banned chats.")
    lines = "\n".join(f"• <code>{c}</code> — {h(r)}" for c, r in chan_bans.items())
    await msg.answer(f"⛔ Banned chats:\n{lines}", parse_mode=ParseMode.HTML)

def split_buttons(raw: str):
    """Lines like [Button text](https://link) become inline buttons; the rest is the message text."""
    text_lines, rows = [], []
    for line in (raw or '').splitlines():
        m = re.match(r'^\s*\[(.+?)\]\((https?://[^\s)]+)\)\s*$', line)
        if m:
            rows.append([make_button(m.group(1), url=m.group(2))])
        else:
            text_lines.append(line)
    markup = InlineKeyboardMarkup(inline_keyboard=rows) if rows else None
    return "\n".join(text_lines).strip(), markup


# ================= SEND-ONLY (DELAYED AUTO-ACCEPT) + DM WELCOME MEDIA + BROADCAST PROGRESS =================
DELAYED_FN = DATA_DIR / 'delayed_approvals.json'
delayed_queue = load_json(DELAYED_FN, [])   # [{chat, uid, due}]
GROUP_SETTING_KEYS['sendonly'] = 'Send-only (delayed accept)'

def _parse_delay_token(token: str):
    return parse_duration(token)

@dp.message(Command('sendonly'), F.chat.type.in_(GROUP_TYPES))
async def cmd_sendonly(msg: types.Message):
    if not await _require_admin(msg):
        return
    parts = (msg.text or '').split()
    chat_s = group_settings.setdefault(str(msg.chat.id), {})
    if len(parts) < 2 or parts[1].lower() not in ('on', 'off'):
        cur = chat_s.get('sendonly_delay', 86400)
        return await msg.reply(f"Usage: /sendonly on [delay]  or  /sendonly off\nDelay examples: 30m, 12h, 1d (default 1d). Current: {cur // 3600} h")
    if parts[1].lower() == 'off':
        chat_s['sendonly'] = False
        save_json(SETTINGS_FN, group_settings)
        return await msg.reply("🔴 Send-only mode OFF. New requests are approved normally.")
    chat_s['sendonly'] = True
    if len(parts) >= 3:
        secs = _parse_delay_token(parts[2])
        if not secs:
            return await msg.reply("❌ Invalid delay. Use 30m, 12h, 1d, 2w.")
        chat_s['sendonly_delay'] = secs
    save_json(SETTINGS_FN, group_settings)
    await msg.reply(f"⏱️ Send-only mode ON: requests are approved after {chat_s.get('sendonly_delay', 86400) // 3600} h.")

async def delayed_approvals_loop():
    """Approves held requests whose timer is up and sends the welcome DM."""
    while True:
        try:
            now = time.time()
            due = [d for d in delayed_queue if d['due'] <= now]
            if due:
                by_chat = {}
                for d in due:
                    by_chat.setdefault(d['chat'], []).append(d['uid'])
                for cid, uids in by_chat.items():
                    done = await approve_users(cid, uids, limits.get(str(cid), {}))
                    for uid in done:
                        await notify_approved(cid, uid)
                    for uid in uids:
                        if uid not in done:
                            record_failure('approve_failed')
                delayed_queue[:] = [d for d in delayed_queue if d['due'] > now]
                save_json(DELAYED_FN, delayed_queue)
        except Exception as e:
            logging.warning(f"Delayed approvals loop error: {e}")
        await asyncio.sleep(60)

# Broadcast live progress + DM welcome with a custom photo
def _dm_media(chat_id: int):
    return group_settings.get(str(chat_id), {}).get('dm_welcome_media')


GROUP_SETTING_KEYS['dm_welcome'] = 'Approval DM'

# ================= GAPS: PAGED GROUP LIST, UNASSIGNED CHATS, SETUP GUIDE =================
GROUPS_PAGE_SIZE = 8

def _groups_page_markup(gs, page: int) -> InlineKeyboardMarkup:
    total_pages = max(1, (len(gs) + GROUPS_PAGE_SIZE - 1) // GROUPS_PAGE_SIZE)
    page = max(0, min(page, total_pages - 1))
    chunk = gs[page * GROUPS_PAGE_SIZE:(page + 1) * GROUPS_PAGE_SIZE]
    rows = [[make_button(title[:40], callback_data=f"grp:open:{cid}", style=BTN_PRIMARY)] for cid, title in chunk]
    nav = []
    if page > 0:
        nav.append(make_button("⬅️ Prev", callback_data=f"grp:list:{page - 1}", style=BTN_PRIMARY))
    nav.append(make_button(f"{page + 1}/{total_pages}", callback_data="grp:noop", style=BTN_PRIMARY))
    if page < total_pages - 1:
        nav.append(make_button("Next ➡️", callback_data=f"grp:list:{page + 1}", style=BTN_PRIMARY))
    rows.append(nav)
    return InlineKeyboardMarkup(inline_keyboard=rows)

@dp.callback_query(lambda c: c.data == 'grp:noop')
async def groups_noop(cb: CallbackQuery):
    await cb.answer()

@dp.callback_query(lambda c: bool(c.data) and c.data.startswith('grp:list:'))
async def groups_page_cb(cb: CallbackQuery):
    try:
        page = int(cb.data.split(':')[2])
    except ValueError:
        page = 0
    gs = await _admin_groups(cb.from_user.id)
    if not gs:
        await cb.answer("No groups.")
        return await cb.message.edit_text("You are not an admin of any registered group yet.")
    await cb.message.edit_text("🛠 <b>Select a group to manage:</b>", reply_markup=_groups_page_markup(gs, page),
                               parse_mode=ParseMode.HTML)
    await cb.answer()

@dp.message(Command('unassigned'), F.chat.type == ChatType.PRIVATE)
async def cmd_unassigned(msg: types.Message):
    """Bot admins: chats whose adder is not recorded (added before owner tracking) or not a bot admin any more."""
    if not is_bot_admin(msg.from_user.id):
        return
    owners = group_settings.get('_owners', {})
    rows = []
    for cid, title in groups.items():
        owner = owners.get(str(cid))
        # unassigned = no recorded adder, or the recorded adder is no longer an admin there
        if owner is None or not await is_chat_admin(int(cid), owner):
            rows.append(f"• {h(str(title))} — <code>{cid}</code> — owner: {owner if owner else 'unknown'}")
    if not rows:
        return await msg.answer("✅ Every connected chat has a recorded owner.", parse_mode=ParseMode.HTML)
    await msg.answer(f"🧩 <b>Unassigned chats ({len(rows)})</b>\n" + "\n".join(rows[:100]), parse_mode=ParseMode.HTML)

SETUP_STEPS = [
    ("1/5 · Add the bot as admin",
     "Open your group or channel, go to Administrators, and add this bot as an <b>admin</b>.\n"
     "Give it <b>Invite users via link</b> and <b>Manage join requests</b> permissions."),
    ("2/5 · Turn on Approval required",
     "In your invite link settings, turn <b>Approval required</b> ON. Only then do join requests reach the bot."),
    ("3/5 · Enable auto-approve",
     "In the group, send <code>/autoapprove</code> and tap <b>Enable</b>. Use <code>/set_mode immediate</code> for instant approval."),
    ("4/5 · Optional: bulk approve",
     "To approve old pending requests, log in privately with <code>/login</code> (OTP and 2FA supported), then use <code>/approve_all</code> in the group."),
    ("5/5 · Test it",
     "Join with a test account. You should be approved and receive the welcome DM. Use <code>/groups</code> in private to tweak features."),
]

def _setup_markup(n: int) -> InlineKeyboardMarkup:
    nav = []
    if n > 1:
        nav.append(make_button("⬅️ Back", callback_data=f"setup:{n - 1}", style=BTN_PRIMARY))
    if n < len(SETUP_STEPS):
        nav.append(make_button("Next ➡️", callback_data=f"setup:{n + 1}", style=BTN_SUCCESS))
    else:
        nav.append(make_button("🏁 Done", callback_data="setup:done", style=BTN_SUCCESS))
    return InlineKeyboardMarkup(inline_keyboard=[nav, [make_button("✕ Close", callback_data="help:close", style=BTN_DANGER)]])

def _setup_text(n: int) -> str:
    title, body = SETUP_STEPS[n - 1]
    return f"🧭 <b>Setup guide</b>\n\n<b>{title}</b>\n\n{body}"

@dp.message(Command('setup'))
async def cmd_setup(msg: types.Message):
    await msg.answer(_setup_text(1), reply_markup=_setup_markup(1), parse_mode=ParseMode.HTML)

@dp.callback_query(lambda c: bool(c.data) and c.data.startswith('setup:'))
async def setup_cb(cb: CallbackQuery):
    token = cb.data.split(':', 1)[1]
    if token == 'done':
        await cb.answer("🎉 You are all set!")
        return await cb.message.edit_text("🎉 <b>Setup complete.</b> Use /groups to manage features and /cmds for all commands.",
                                          parse_mode=ParseMode.HTML)
    try:
        n = max(1, min(len(SETUP_STEPS), int(token)))
    except ValueError:
        return await cb.answer()
    await cb.answer()
    await cb.message.edit_text(_setup_text(n), reply_markup=_setup_markup(n), parse_mode=ParseMode.HTML)


# ================= DM TEMPLATE: PLACEHOLDERS, INLINE BUTTON SYNTAX, BACKLOG PROGRESS =================
_BTN_GROUP = re.compile(r'\[([^\[\]]+)\]')
_BTN_PART = re.compile(r'^\s*(.+?)\s*-\s*((?:https?|tg)://\S+?)\s*$')

def split_inline_buttons(template: str):
    """Lines made only of [Text - https://link] groups become button rows (groups on one line share a row).
    Returns (plain_text, InlineKeyboardMarkup or None)."""
    rows, text_lines = [], []
    for line in template.splitlines():
        stripped = line.strip()
        groups = _BTN_GROUP.findall(stripped)
        if groups and _BTN_GROUP.sub('', stripped).strip() == '':
            row, ok = [], True
            for g in groups:
                for part in g.split('|'):
                    m = _BTN_PART.match(part)
                    if not m:
                        ok = False
                        break
                    row.append(make_button(m.group(1).strip(), url=m.group(2)))
                if not ok:
                    break
            if ok and row:
                rows.append(row)
                continue
        text_lines.append(line)
    text = "\n".join(text_lines).strip()
    return text, (InlineKeyboardMarkup(inline_keyboard=rows) if rows else None)

def render_dm_placeholders(body: str, full: str, username, chat_title: str, uid: int) -> str:
    first = full.split()[0] if full.split() else full
    handle = f"@{username}" if username else first
    mention = f"<a href=\"tg://user?id={uid}\">{h(full)}</a>"
    last = full.split()[-1] if len(full.split()) > 1 else ''
    return (body.replace('{name}', h(full)).replace('{first_name}', h(first)).replace('{first}', h(first))
                .replace('{last_name}', h(last)).replace('{channel}', h(chat_title))
                .replace('{username}', h(handle)).replace('{mention}', mention)
                .replace('{chat_title}', h(chat_title)).replace('{chat}', h(chat_title))
                .replace('{user_id}', str(uid)))

async def approve_with_progress(cb, cid: int, ids: list):
    done_total, chunk = [], 10
    stop_flags.discard(cid)
    for i in range(0, len(ids), chunk):
        if cid in stop_flags:
            break
        part = ids[i:i + chunk]
        done = await approve_users(cid, part, limits.get(str(cid), {}))
        for uid in done:
            await notify_approved(cid, uid)
        done_total.extend(done)
        try:
            await cb.message.edit_text(
                f"⚡ Approving... {min(i + chunk, len(ids))}/{len(ids)} (approved: {len(done_total)})",
                reply_markup=stop_markup(cid))
        except Exception:
            pass
    stop_flags.discard(cid)
    return done_total

@dp.callback_query(lambda c: bool(c.data) and c.data.startswith('bulk:stop:'))
async def bulk_stop_cb(cb: CallbackQuery):
    cid = int(cb.data.split(':')[2])
    if not await is_chat_admin(cid, cb.from_user.id):
        return await cb.answer("⛔ Admins only.", show_alert=True)
    stop_flags.add(cid)
    await cb.answer("Stopping after the current batch...")

@dp.callback_query(lambda c: bool(c.data) and c.data.startswith('pend:ask:'))
async def pending_confirm(cb: CallbackQuery):
    cid = int(cb.data.split(':')[2])
    if not await is_chat_admin(cid, cb.from_user.id):
        return await cb.answer("⛔ Admins only.", show_alert=True)
    ids = await fetch_pending_user_ids(cid, limits.get(str(cid), {}))
    if not ids:
        return await cb.answer("No pending requests.", show_alert=True)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [make_button(f"⚡ Yes, approve all ({len(ids)})", callback_data=f"pend:all:{cid}", style=BTN_SUCCESS)],
        [make_button("✕ Cancel", callback_data="help:close", style=BTN_DANGER)],
    ])
    await cb.answer()
    await cb.message.answer(f"⚠️ Approve all {len(ids)} pending request(s) in this chat?", reply_markup=kb)


# ================= DM AUTO-DELETE TIMER + CHANNEL CSV EXPORT =================
DM_DELETE_CHOICES = {'10s': 10, '30s': 30, '1m': 60, '5m': 300}

@dp.message(Command('dmdelete'), F.chat.type.in_(GROUP_TYPES))
async def cmd_dmdelete(msg: types.Message):
    """Auto-delete the approval DM after a timer: /dmdelete 10s|30s|1m|5m|never"""
    if not await _require_admin(msg):
        return
    parts = (msg.text or '').split()
    chat_s = group_settings.setdefault(str(msg.chat.id), {})
    current = int(chat_s.get('dm_delete_after', 0) or 0)
    if len(parts) < 2:
        label = 'never' if current == 0 else f"{current} s"
        return await msg.reply(f"Approval DM auto-delete: <b>{label}</b>\nUsage: /dmdelete 10s | 30s | 1m | 5m | never",
                               parse_mode=ParseMode.HTML)
    choice = parts[1].lower()
    if choice == 'never':
        seconds = 0
    elif choice in DM_DELETE_CHOICES:
        seconds = DM_DELETE_CHOICES[choice]
    else:
        return await msg.reply("❌ Use one of: 10s, 30s, 1m, 5m, never")
    chat_s['dm_delete_after'] = seconds
    save_json(SETTINGS_FN, group_settings)
    await msg.reply("✅ Approval DM will " + ("stay forever." if seconds == 0 else f"be deleted after {choice}."))

def channels_csv_bytes() -> bytes:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(['chat_id', 'title', 'auto_approve', 'mode', 'added_by'])
    owners = group_settings.get('_owners', {})
    for cid, title in groups.items():
        writer.writerow([cid, title, chat_setting(int(cid), 'autoapprove'),
                         limits.get(str(cid), {}).get('mode', ''), owners.get(str(cid), '')])
    return buf.getvalue().encode('utf-8')

@dp.message(Command('exportchannels'), F.chat.type == ChatType.PRIVATE)
async def cmd_exportchannels(msg: types.Message):
    if not is_bot_admin(msg.from_user.id):
        return
    await msg.answer_document(BufferedInputFile(channels_csv_bytes(), filename='channels.csv'),
                              caption=f"📄 {len(groups)} channel(s) exported.")


# ================= STOP CONTROL, STYLED LEAVE DM, PYTHON VERSION =================
import platform
stop_flags = set()          # chat ids whose running bulk approval should stop
GROUP_SETTING_KEYS['leave_dm'] = 'Leave DM with rejoin link'

def stop_markup(cid: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        make_button("⛔ Stop", callback_data=f"bulk:stop:{cid}", style=BTN_DANGER)]])

async def send_leave_dm(chat, user):
    """Styled DM to the member who left, with a rejoin link (if the bot can make one)."""
    if not chat_setting(chat.id, 'leave_dm') or user.is_bot:
        return
    link = None
    try:
        link = await bot.export_chat_invite_link(chat.id)
    except Exception:
        pass
    link = link or (f"https://t.me/{chat.username}" if chat.username else None)
    if not link:
        return
    text = (f"👋 Hey <b>{h(user.first_name or 'there')}</b>!\n\n"
            f"You left <b>{h(chat.title or 'the group')}</b>.\n"
            "Miss us? Tap below to rejoin.")
    kb = InlineKeyboardMarkup(inline_keyboard=[[make_button("🔗 Rejoin", url=link, style=BTN_SUCCESS)]])
    try:
        await bot.send_message(user.id, text, reply_markup=kb, parse_mode=ParseMode.HTML)
    except Exception:
        pass  # user never started the bot, or blocked it

def python_info() -> str:
    return platform.python_version()


# ================= BROADCAST CONFIRMATION, USER CARD, CHAT PERMISSIONS =================
BROADCAST_JOBS = {}                 # admin uid -> pending broadcast job
BCAST_TTL_LABELS = {'never': 'never', '1h': '1 hour', '1d': '1 day'}
BCAST_TTL_SECONDS = {'never': 0, '1h': 3600, '1d': 86400}
USER_APPR_FN = DATA_DIR / 'user_approvals.json'
user_approvals = load_json(USER_APPR_FN, {})   # uid(str) -> approvals received

def _bcast_preview_text(job) -> str:
    kind = "pinned in every DM" if job['pin'] else "sent to every user"
    ttl = BCAST_TTL_LABELS.get(job.get('ttl_key', 'never'), 'never')
    return (f"📣 <b>Broadcast preview</b>\n"
            f"Recipients: <b>{len(accepted_users)}</b> user(s), {kind}.\n"
            f"Auto-delete: <b>{ttl}</b>\n\nChoose the auto-delete timer, then send.")

def _bcast_markup(job) -> InlineKeyboardMarkup:
    cur = job.get('ttl_key', 'never')
    def ttl_btn(key):
        label = BCAST_TTL_LABELS[key] + (" ✓" if cur == key else "")
        return make_button(label, callback_data=f"bc:ttl:{key}", style=BTN_PRIMARY)
    return InlineKeyboardMarkup(inline_keyboard=[
        [ttl_btn('never'), ttl_btn('1h'), ttl_btn('1d')],
        [make_button("✅ Send", callback_data="bc:go", style=BTN_SUCCESS),
         make_button("❌ Cancel", callback_data="bc:no", style=BTN_DANGER)],
    ])

async def _start_broadcast(msg: types.Message, pin: bool):
    src = msg.reply_to_message
    _, markup = split_buttons(msg.text or '')
    if src:
        job = {'src_chat': msg.chat.id, 'src_mid': src.message_id, 'body': None}
    else:
        parts = (msg.text or '').split(maxsplit=1)
        if len(parts) < 2:
            cmd = 'pbroadcast' if pin else 'broadcast'
            return await msg.answer(f"Usage: reply to a message with /{cmd}, or /{cmd} <text>")
        body, _ = split_buttons(parts[1])
        job = {'src_chat': None, 'src_mid': None, 'body': body}
    job.update({'markup': markup, 'pin': pin, 'ttl_key': 'never'})
    BROADCAST_JOBS[msg.from_user.id] = job
    # Show the admin exactly what will be sent
    if job['src_mid'] is not None:
        await bot.copy_message(msg.chat.id, from_chat_id=job['src_chat'], message_id=job['src_mid'])
    else:
        await bot.send_message(msg.chat.id, job['body'], parse_mode=None)
    await msg.answer(_bcast_preview_text(job), reply_markup=_bcast_markup(job), parse_mode=ParseMode.HTML)

async def _delete_message_later(chat_id: int, message_id: int, delay: int):
    await asyncio.sleep(delay)
    try:
        await bot.delete_message(chat_id, message_id)
    except Exception:
        pass

async def execute_broadcast(job, status_msg):
    ok = fail = 0
    ttl = BCAST_TTL_SECONDS.get(job.get('ttl_key', 'never'), 0)
    for uid in list(accepted_users):
        try:
            if job['src_mid'] is not None:
                sent = await bot.copy_message(uid, from_chat_id=job['src_chat'], message_id=job['src_mid'],
                                              reply_markup=job['markup'])
            else:
                sent = await bot.send_message(uid, job['body'], parse_mode=None, reply_markup=job['markup'])
            mid = sent.message_id
            if job['pin']:
                try:
                    await bot.pin_chat_message(uid, mid, disable_notification=True)
                except Exception:
                    pass  # pinning is best-effort
            if ttl:
                task = asyncio.create_task(_delete_message_later(uid, mid, ttl))
                _background_tasks.add(task)
                task.add_done_callback(_background_tasks.discard)
            ok += 1
        except Exception:
            fail += 1
        if (ok + fail) % 25 == 0:
            try:
                await status_msg.edit_text(f"📡 Broadcasting... {ok + fail}/{len(accepted_users)} (failed: {fail})")
            except Exception:
                pass
        await asyncio.sleep(0.05)
    tail = f" Auto-delete after {BCAST_TTL_LABELS.get(job.get('ttl_key', 'never'))}." if ttl else ""
    await status_msg.edit_text(f"✅ Broadcast done. Sent: {ok}, failed: {fail}.{tail}")

@dp.callback_query(lambda c: bool(c.data) and c.data.startswith('bc:'))
async def broadcast_confirm_cb(cb: CallbackQuery):
    uid = cb.from_user.id
    if not is_bot_admin(uid):
        return await cb.answer("⛔ Admins only.", show_alert=True)
    action = cb.data.split(':', 2)[1]
    job = BROADCAST_JOBS.get(uid)
    if action == 'ttl':
        key = cb.data.split(':', 2)[2]
        if not job or key not in BCAST_TTL_SECONDS:
            return await cb.answer("No pending broadcast.", show_alert=True)
        job['ttl_key'] = key
        await cb.answer()
        return await cb.message.edit_text(_bcast_preview_text(job), reply_markup=_bcast_markup(job), parse_mode=ParseMode.HTML)
    if not job:
        return await cb.answer("No pending broadcast.", show_alert=True)
    if action == 'no':
        BROADCAST_JOBS.pop(uid, None)
        await cb.answer("Cancelled")
        return await cb.message.edit_text("❌ Broadcast cancelled.")
    if action == 'go':
        BROADCAST_JOBS.pop(uid, None)
        await cb.answer("Broadcasting...")
        status = await cb.message.edit_text("📡 Broadcasting...")
        await execute_broadcast(job, status)

def _user_card_markup(uid: int) -> InlineKeyboardMarkup:
    if is_banned(uid):
        act = make_button("✅ Unban", callback_data=f"usr:unban:{uid}", style=BTN_SUCCESS)
    else:
        act = make_button("🚫 Ban", callback_data=f"usr:ban:{uid}", style=BTN_DANGER)
    return InlineKeyboardMarkup(inline_keyboard=[[act],
        [make_button("🔄 Refresh", callback_data=f"usr:show:{uid}", style=BTN_PRIMARY)]])

async def user_card_text(uid: int) -> str:
    try:
        chat = await bot.get_chat(uid)
        name, uname = chat.full_name or str(uid), chat.username
    except Exception:
        name, uname = str(uid), None
    seen = user_last_seen.get(str(uid))
    seen_txt = datetime.fromtimestamp(seen, timezone.utc).strftime('%Y-%m-%d %H:%M UTC') if seen else 'never'
    if is_banned(uid):
        until = bans.get(str(uid), {}).get('until')
        when = 'permanent' if not until else 'until ' + datetime.fromtimestamp(until, timezone.utc).strftime('%Y-%m-%d %H:%M')
        ban_txt = f"banned ({when})"
    else:
        ban_txt = "not banned"
    return (f"👤 <b>{h(name)}</b>\n"
            f"ID: <code>{uid}</code>\n"
            f"Username: {'@' + h(uname) if uname else 'none'}\n"
            f"Last seen: {seen_txt}\n"
            f"Accepted: {'yes' if uid in accepted_users else 'no'}\n"
            f"Approvals received: <b>{user_approvals.get(str(uid), 0)}</b>\n"
            f"Status: {ban_txt}\n\n"
            f"To message this user: <code>/send {uid}</code> (reply to a message).")

@dp.message(Command('user'), F.chat.type == ChatType.PRIVATE)
async def cmd_user(msg: types.Message):
    if not is_bot_admin(msg.from_user.id):
        return
    target = await _target_user(msg)
    if not target:
        return await msg.answer("Usage: /user &lt;id or @username&gt;  or reply to a user", parse_mode=ParseMode.HTML)
    await msg.answer(await user_card_text(target.id), reply_markup=_user_card_markup(target.id), parse_mode=ParseMode.HTML)

@dp.callback_query(lambda c: bool(c.data) and c.data.startswith('usr:'))
async def user_card_cb(cb: CallbackQuery):
    if not is_bot_admin(cb.from_user.id):
        return await cb.answer("⛔ Admins only.", show_alert=True)
    _, action, uid_s = cb.data.split(':', 2)
    uid = int(uid_s)
    if action == 'ban':
        bans[str(uid)] = {'until': None, 'reason': 'banned from user card'}
        save_json(BANS_FN, bans)
    elif action == 'unban':
        bans.pop(str(uid), None)
        save_json(BANS_FN, bans)
    await cb.answer("Done")
    await cb.message.edit_text(await user_card_text(uid), reply_markup=_user_card_markup(uid), parse_mode=ParseMode.HTML)

CHAT_PERMS = {
    'lock': ChatPermissions(can_send_messages=False, can_send_audios=False, can_send_documents=False,
                            can_send_photos=False, can_send_videos=False, can_send_video_notes=False,
                            can_send_voice_notes=False, can_send_polls=False, can_send_other_messages=False,
                            can_add_web_page_previews=False, can_invite_users=False, can_pin_messages=False,
                            can_change_info=False),
    'nomedia': ChatPermissions(can_send_messages=True, can_send_audios=False, can_send_documents=False,
                               can_send_photos=False, can_send_videos=False, can_send_video_notes=False,
                               can_send_voice_notes=False, can_send_polls=False, can_send_other_messages=False,
                               can_add_web_page_previews=False),
    'open': ChatPermissions(can_send_messages=True, can_send_audios=True, can_send_documents=True,
                            can_send_photos=True, can_send_videos=True, can_send_video_notes=True,
                            can_send_voice_notes=True, can_send_polls=True, can_send_other_messages=True,
                            can_add_web_page_previews=True, can_invite_users=True, can_pin_messages=False,
                            can_change_info=False),
}

@dp.message(Command('chatperms'), F.chat.type.in_(GROUP_TYPES))
async def cmd_chatperms(msg: types.Message):
    """Default permissions for every member, including new joiners: /chatperms lock|nomedia|open"""
    if not await _require_admin(msg):
        return
    parts = (msg.text or '').split()
    if len(parts) < 2 or parts[1].lower() not in CHAT_PERMS:
        cur = group_settings.get(str(msg.chat.id), {}).get('chatperms', 'open')
        return await msg.reply(f"Current: <b>{cur}</b>\nUsage: /chatperms lock | nomedia | open\n"
                               "lock = no posting · nomedia = text only · open = everything",
                               parse_mode=ParseMode.HTML)
    mode = parts[1].lower()
    try:
        await bot.set_chat_permissions(msg.chat.id, CHAT_PERMS[mode])
    except Exception as e:
        return await msg.reply(f"❌ Could not change permissions: {h(str(e))}\nThe bot needs the 'Restrict members' right.",
                               parse_mode=ParseMode.HTML)
    group_settings.setdefault(str(msg.chat.id), {})['chatperms'] = mode
    save_json(SETTINGS_FN, group_settings)
    await msg.reply(f"✅ Default permissions set to <b>{mode}</b> for all members.", parse_mode=ParseMode.HTML)


# ================= STALE PENDING REQUEST AUTO-DECLINE =================
# Requests older than the chat's limit (in hours) are declined automatically.
# Only requests this bot has seen are tracked (pending_reqs), so requests from before this
# feature existed are not affected.

@dp.message(Command('stalecleanup'), F.chat.type.in_(GROUP_TYPES))
async def cmd_stalecleanup(msg: types.Message):
    """Auto-decline pending requests older than N hours: /stalecleanup 48 | off"""
    if not await _require_admin(msg):
        return
    parts = (msg.text or '').split()
    chat_s = group_settings.setdefault(str(msg.chat.id), {})
    current = int(chat_s.get('stale_hours', 0) or 0)
    if len(parts) < 2:
        label = 'off' if current == 0 else f"{current} h"
        return await msg.reply(f"Stale request cleanup: <b>{label}</b>\n"
                               "Usage: /stalecleanup &lt;hours&gt; (e.g. 48)  or  /stalecleanup off",
                               parse_mode=ParseMode.HTML)
    arg = parts[1].lower()
    if arg == 'off':
        chat_s['stale_hours'] = 0
        reply = "✅ Stale request cleanup is OFF."
    elif arg.isdigit() and int(arg) >= 1:
        chat_s['stale_hours'] = int(arg)
        reply = f"✅ Pending requests older than {int(arg)} h will be declined automatically."
    else:
        return await msg.reply("❌ Give a whole number of hours (1 or more), or 'off'.")
    save_json(SETTINGS_FN, group_settings)
    await msg.reply(reply)

async def stale_cleanup_once():
    now = time.time()
    by_chat = {}
    for key, ts in list(pending_reqs.items()):
        chat_s, uid_s = key.split(':', 1)
        hours = int(group_settings.get(chat_s, {}).get('stale_hours', 0) or 0)
        if hours and now - ts >= hours * 3600:
            by_chat.setdefault(int(chat_s), []).append(int(uid_s))
    for cid, uids in by_chat.items():
        declined = await decline_users(cid, uids, limits.get(str(cid), {}))
        for uid in uids:
            clear_pending_req(cid, uid)
        if declined:
            await log_event(f"🧹 Declined {len(declined)} stale request(s) in <code>{cid}</code>.")

async def stale_cleanup_loop():
    """Runs every 10 minutes; does nothing for chats where the limit is off."""
    while True:
        try:
            await stale_cleanup_once()
        except Exception as e:
            logging.warning(f"Stale cleanup error: {e}")
        await asyncio.sleep(600)


# ================= SETTINGS BACKUP AND RESTORE =================
BACKUP_VERSION = 1
RESTORE_PENDING = {}   # admin uid -> parsed backup waiting for confirmation

def build_backup() -> bytes:
    data = {
        'version': BACKUP_VERSION,
        'created_at': datetime.now(timezone.utc).isoformat(),
        'settings': group_settings,
        'bans': bans,
        'channels': {
            'groups': groups,
            'limits': limits,
            'force_sub': FORCE_SUB_CHANNELS,
            'chan_bans': chan_bans,
        },
        'admins': {
            'bot_admins': sorted(bot_admins),
            'web_admins': web_admins,
        },
        'autoposts': autoposts,
        'leave_noti_users': sorted(leave_noti_users),
        'accepted_users': sorted(accepted_users),
    }
    return json.dumps(data, indent=2, ensure_ascii=False).encode('utf-8')

def validate_backup(data) -> str:
    """Returns an error message, or '' if the backup looks valid."""
    if not isinstance(data, dict) or data.get('version') != BACKUP_VERSION:
        return "This is not a backup file for this bot (wrong or missing version)."
    for key in ('settings', 'bans', 'channels', 'admins'):
        if not isinstance(data.get(key), dict):
            return f"Backup is missing the '{key}' section."
    return ''

def apply_backup(data: dict):
    """Replaces the current settings with the backup and saves everything to storage."""
    def replace_dict(target, src):
        target.clear()
        target.update(src)
    ch = data.get('channels', {})
    ad = data.get('admins', {})
    replace_dict(group_settings, data.get('settings', {}))
    replace_dict(bans, data.get('bans', {}))
    replace_dict(groups, ch.get('groups', {}))
    replace_dict(limits, ch.get('limits', {}))
    replace_dict(chan_bans, ch.get('chan_bans', {}))
    FORCE_SUB_CHANNELS[:] = ch.get('force_sub', [])
    bot_admins.clear()
    bot_admins.update(int(x) for x in ad.get('bot_admins', []))
    replace_dict(web_admins, ad.get('web_admins', {}))
    autoposts[:] = data.get('autoposts', [])
    leave_noti_users.clear()
    leave_noti_users.update(int(x) for x in data.get('leave_noti_users', []))
    accepted_users.clear()
    accepted_users.update(int(x) for x in data.get('accepted_users', []))
    # persist everything
    save_json(SETTINGS_FN, group_settings)
    save_json(BANS_FN, bans)
    save_json(CHAN_BANS_FN, chan_bans)
    save_json(FSUB_FN, FORCE_SUB_CHANNELS)
    save_json(BOT_ADMINS_FN, list(bot_admins))
    save_json(WEB_ADMINS_FN, web_admins)
    save_json(AUTOPOST_FN, autoposts)
    save_json(LEAVE_NOTI_FN, list(leave_noti_users))
    save_state()   # accepted users, groups and limits

@dp.message(Command('backup'), F.chat.type == ChatType.PRIVATE)
async def cmd_backup(msg: types.Message):
    if not is_bot_admin(msg.from_user.id):
        return
    name = f"backup-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M')}.json"
    await msg.answer_document(
        BufferedInputFile(build_backup(), filename=name),
        caption="💾 Backup of settings, bans, channels and admins.\n"
                "Keep it private: it includes admin password hashes. Restore with /restore (reply to this file).")

@dp.message(Command('restore'), F.chat.type == ChatType.PRIVATE)
async def cmd_restore(msg: types.Message):
    if not is_bot_admin(msg.from_user.id):
        return
    doc = msg.reply_to_message.document if msg.reply_to_message else None
    if not doc or not (doc.file_name or '').endswith('.json'):
        return await msg.answer("Reply to a backup .json file with /restore.")
    buf = io.BytesIO()
    file = await bot.get_file(doc.file_id)
    await bot.download_file(file.file_path, destination=buf)
    try:
        data = json.loads(buf.getvalue().decode('utf-8'))
    except Exception:
        return await msg.answer("❌ Could not read that file as JSON.")
    problem = validate_backup(data)
    if problem:
        return await msg.answer(f"❌ {h(problem)}", parse_mode=ParseMode.HTML)
    RESTORE_PENDING[msg.from_user.id] = data
    summary = (f"♻️ <b>Restore preview</b>\n"
               f"Backup from: {h(str(data.get('created_at', 'unknown')))}\n"
               f"Chats: {len(data['channels'].get('groups', {}))} · Chat settings: {len(data['settings'])}\n"
               f"Bans: {len(data['bans'])} · Bot admins: {len(data['admins'].get('bot_admins', []))}\n"
               f"Users: {len(data.get('accepted_users', []))}\n\n"
               "This replaces the current settings, bans, channels and admins.")
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        make_button("✅ Restore now", callback_data="rst:go", style=BTN_SUCCESS),
        make_button("✕ Cancel", callback_data="rst:no", style=BTN_DANGER)]])
    await msg.answer(summary, reply_markup=kb, parse_mode=ParseMode.HTML)

@dp.callback_query(lambda c: bool(c.data) and c.data.startswith('rst:'))
async def restore_confirm_cb(cb: CallbackQuery):
    uid = cb.from_user.id
    if not is_bot_admin(uid):
        return await cb.answer("⛔ Admins only.", show_alert=True)
    data = RESTORE_PENDING.pop(uid, None)
    if cb.data == 'rst:no' or data is None:
        await cb.answer("Cancelled")
        return await cb.message.edit_text("❌ Restore cancelled.")
    try:
        apply_backup(data)
    except Exception as e:
        logging.error(f"Restore failed: {e}")
        return await cb.message.edit_text(f"❌ Restore failed: {h(str(e))}", parse_mode=ParseMode.HTML)
    await cb.answer("Restored")
    await cb.message.edit_text("✅ Backup restored. Settings, bans, channels and admins are back.")


@dp.callback_query(lambda c: bool(c.data) and c.data.startswith('ap:'))
async def autopost_buttons_cb(cb: CallbackQuery):
    if not is_bot_admin(cb.from_user.id):
        return await cb.answer("⛔ Admins only.", show_alert=True)
    _, action, pid_s = cb.data.split(':', 2)
    post = next((p for p in autoposts if str(p['id']) == pid_s), None)
    if not post:
        return await cb.answer("That auto-post no longer exists.", show_alert=True)
    if action == 'tog':
        post['paused'] = not post.get('paused', False)
        save_json(AUTOPOST_FN, autoposts)
        await cb.answer("Paused" if post['paused'] else "Resumed")
    elif action == 'del':
        autoposts[:] = [p for p in autoposts if str(p['id']) != pid_s]
        save_json(AUTOPOST_FN, autoposts)
        await cb.answer("Deleted")
    await cb.message.edit_text("📅 Auto-posts updated. Send /autopost list to refresh.")

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
    register_admin_web(app)
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', int(port)).start()
    logging.info(f"Health server listening on port {port}")

async def main():
    print('🤖 AK AUTO REQUEST BOT is started!')
    print('👨🏻‍💻 Dev : Anuj Kumar')
    
    await get_bot_username()
    
    for chat_id_str, cfg in limits.items():
        try:
            if cfg.get('mode') != 'time':
                await process_pending_requests(int(chat_id_str), cfg)
        except Exception as e:
            logging.warning(f"Error processing pending requests for chat {chat_id_str}: {e}")
    
    _background_tasks.add(asyncio.create_task(time_mode_loop()))  # keep a reference (no garbage collection)
    
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
        BotCommand(command="settings", description="⚙️ Settings"),
    ]
    await bot.set_my_commands(commands)
    # Admin-only menu for the owner and bot admins (not shown to normal users)
    from aiogram.types import BotCommandScopeChat
    admin_cmds = commands + [
        BotCommand(command="stats", description="📊 Bot stats"),
        BotCommand(command="analytics", description="📈 Approvals, last 7 days"),
        BotCommand(command="setlog", description="📝 Set activity log channel"),
        BotCommand(command="unjoined", description="🔍 Users not in force-sub channels"),
        BotCommand(command="fjoin", description="📢 Manage force-sub channels"),
        BotCommand(command="chats", description="📡 Connected chats"),
        BotCommand(command="users", description="👥 User list"),
        BotCommand(command="broadcast", description="📣 Broadcast to all users"),
        BotCommand(command="pbroadcast", description="📌 Broadcast and pin"),
        BotCommand(command="admin", description="🛠 Admin control panel"),
        BotCommand(command="admins", description="👑 Bot admins"),
        BotCommand(command="restart", description="🔄 Restart the bot"),
        BotCommand(command="autopost", description="📅 Scheduled auto-posts"),
        BotCommand(command="chanban", description="⛔ Ban a chat (bot ignores it)"),
        BotCommand(command="user", description="👤 User card"),
        BotCommand(command="backup", description="💾 Backup settings"),
        BotCommand(command="restore", description="♻️ Restore from a backup file"),
    ]
    for admin_id in {OWNER_ID, *bot_admins}:
        try:
            await bot.set_my_commands(admin_cmds, scope=BotCommandScopeChat(chat_id=admin_id))
        except Exception as e:
            logging.warning(f"Could not set admin menu for {admin_id}: {e}")
    print("✅ Bot commands menu registered!")
    
    for info in list(captcha_pending.values()):
        key = (info['chat'], info['uid'])
        if key in _captcha_tasks:
            continue
        remaining = info.get('expires', 0) - time.time()
        _captcha_tasks[key] = asyncio.create_task(captcha_timeout(info['chat'], info['uid'], remaining))
    _background_tasks.add(asyncio.create_task(autopost_loop()))
    _background_tasks.add(asyncio.create_task(delayed_approvals_loop()))
    _background_tasks.add(asyncio.create_task(stale_cleanup_loop()))
    await start_health_server()
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
