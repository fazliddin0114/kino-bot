import logging
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import (
    ReplyKeyboardMarkup, 
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    Message,
    ReplyKeyboardRemove,
    ForceReply
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from datetime import datetime
from aiogram.filters import StateFilter
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram import exceptions

# Logging sozlamalari
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Konfiguratsiya
class Config:
    # Reklama va majburiy obuna kanali
    CHANNEL_USERNAME = "ajoyib_kino_kodlari1"
    CHANNEL_LINK = "https://t.me/ajoyib_kino_kodlari1"
    CHANNEL_ID = -1002341118048
    
    # Maxfiy kino kanali (faqat admin biladi)
    SECRET_CHANNEL_USERNAME = "maxfiy_kino_kanal"
    SECRET_CHANNEL_LINK = "https://t.me/maxfiy_kino_kanal"
    SECRET_CHANNEL_ID = -1002537276349
    
    BOT_TOKEN = "7808158374:AAGMY8mkb0HVi--N2aJyRrPxrjotI6rnm7k"
    ADMIN_IDS = [7871012050, 7183540853 ]  # Adminlar ro'yxati
    
    # Majburiy obuna kanallari
    REQUIRED_CHANNELS = ["@ajoyib_kino_kodlari1"]

# Botni ishga tushirish
bot = Bot(token=Config.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# Kino qo'shish holatlari
class AddMovieStates(StatesGroup):
    waiting_for_title = State()
    waiting_for_file = State()

# Obunani tekshirish funksiyasi
async def check_subscription(user_id: int) -> bool:
    """Foydalanuvchi barcha kanallarga obuna bo'lganligini tekshirish"""
    for channel in Config.REQUIRED_CHANNELS:
        try:
            chat_member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
            if chat_member.status in ["left", "kicked"]:
                return False
        except Exception as e:
            logger.error(f"Obunani tekshirishda xato (channel: {channel}): {e}")
            return False
    return True

async def ask_for_subscription(message: types.Message):
    """Foydalanuvchidan obuna bo'lishini so'rash"""
    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"🔗 {channel}", url=f"https://t.me/{channel[1:]}")] 
            for channel in Config.REQUIRED_CHANNELS
        ] + [[InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_subs")]]
    )
    await message.answer(
        "Botdan foydalanish uchun quyidagi kanallarga obuna bo'ling:",
        reply_markup=markup
    )

# Start komandasi
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    user_id = message.from_user.id
    
    if not await check_subscription(user_id):
        await ask_for_subscription(message)
    else:
        await message.answer(
            "Xush kelibsiz! Botdan foydalanishingiz mumkin. Kino kodini kiriting\n\n"
        )

# Obunani tekshirish callback
@dp.callback_query(lambda call: call.data == "check_subs")
async def check_subs_callback(call: types.CallbackQuery):
    user_id = call.from_user.id
    if await check_subscription(user_id):
        await call.message.edit_text(
            "Rahmat! Siz barcha kanallarga obuna bo'lgansiz. Botdan foydalanishingiz mumkin."
        )
    else:
        await call.answer(
            "Siz hali ham barcha kanallarga obuna bo'lmagansiz!", 
            show_alert=True
        )

# Admin uchun file_id olish
@dp.message(F.video | F.photo | F.document | F.audio | F.voice)
async def get_file_id(message: types.Message):
    user_id = message.from_user.id

    # Faqat adminlarga ruxsat beramiz
    if user_id in Config.ADMIN_IDS:
        if message.video:
            await message.answer(f"📹 Video File ID: `{message.video.file_id}`")
        elif message.photo:
            await message.answer(f"🖼 Photo File ID: `{message.photo[-1].file_id}`")
        elif message.document:
            await message.answer(f"📄 Document File ID: `{message.document.file_id}`")
        elif message.audio:
            await message.answer(f"🎵 Audio File ID: `{message.audio.file_id}`")
        elif message.voice:
            await message.answer(f"🎙 Voice File ID: `{message.voice.file_id}`")
    else:
        await message.answer("🚫 Ushbu buyruq faqat adminlar uchun mavjud!")

# Kino yuborish funksiyasi
async def send_movie_to_user(message: types.Message, movie_code: str):
    user_id = message.from_user.id
    
    # Obunani tekshirish
    if not await check_subscription(user_id):
        await ask_for_subscription(message)
        return
    
    # Kino kodiga mos fayl ID ni topish
    # Bu yerda sizning kinolar bazangizdan foydalanishingiz mumkin
    # Men soddalik uchun bir nechta misol keltiraman
    movie_data = {
        "1": {"file_id": "BAACAgIAAxkBAAIHx2fRKTCDyuvIluoudQ2T-ZbX0GixAAIKSgACk92xSBCUKpTxyUBSNgQ", "caption": "🎬 Isquvar 4 Megre"},
        "2": {"file_id": "BAACAgIAAxkBAAIIXmfRkQe74Mttq_xUjlRKgZgy5clIAAIlZAACnkFZSHYxfacQG1U3NgQ", "caption": "🎬 Labirint 1"},
        # ... barcha kinolar uchun shu tartibda davom eting
    }
    
    if movie_code in movie_data:
        try:
            await message.answer_video(
                movie_data[movie_code]["file_id"],
                caption=movie_data[movie_code]["caption"]
            )
        except Exception as e:
            logger.error(f"Video yuborishda xato: {e}")
            await message.answer("❌ Video yuborishda xatolik yuz berdi. Iltimos, keyinroq urunib ko'ring.")
    else:
        await message.answer("❌ Bunday kodli kino topilmadi!")

# Har bir kino kodiga alohida handler
for i in range(1, 38):
    @dp.message(F.text == str(i))
    async def movie_handler(message: types.Message):
        await send_movie_to_user(message, message.text)

# Admin paneli
@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    if message.from_user.id not in Config.ADMIN_IDS:
        await message.answer("❌ Siz admin emassiz!")
        return

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎬 Kino qo'shish")],
            [KeyboardButton(text="🏠 Asosiy menyu")]
        ],
        resize_keyboard=True,
    )
    await message.answer("👋 Admin paneliga xush kelibsiz!", reply_markup=keyboard)

# Kino qo'shishni boshlash
@dp.message(F.text == "🎬 Kino qo'shish")
async def start_adding_movie(message: Message, state: FSMContext):
    if message.from_user.id not in Config.ADMIN_IDS:
        await message.answer("❌ Sizda bunday huquq yo'q!")
        return
    
    await message.answer(
        "📝 Kino nomini kiriting:",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(AddMovieStates.waiting_for_title)

# Kino nomi qabul qilish
@dp.message(AddMovieStates.waiting_for_title)
async def process_movie_title(message: Message, state: FSMContext):
    if len(message.text) > 100:
        await message.answer("❌ Kino nomi juda uzun! Iltimos, qisqaroq nom yuboring.")
        return
        
    await state.update_data(movie_title=message.text)
    
    await message.answer(
        f"✅ Kino nomi: {message.text}\n\n"
        "📤 Kino faylini yuboring (video yoki dokument):",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(AddMovieStates.waiting_for_file)

# Kino faylini qabul qilish va maxfiy kanalga joylash
@dp.message(AddMovieStates.waiting_for_file, F.video | F.document)
async def handle_movie_file(message: Message, state: FSMContext):
    data = await state.get_data()
    movie_title = data['movie_title']
    
    if message.video:
        file = message.video
        file_type = "video"
    else:
        file = message.document
        file_type = "document"
    
    try:
        # Avtomatik kod generatsiya
        movie_code = str(len(Config.REQUIRED_CHANNELS) + str(message.from_user.id)[-4:] + str(message.message_id)[-3:])
        
        # Maxfiy kanalga yuborish
        if file_type == "video":
            sent_msg = await bot.send_video(
                chat_id=Config.SECRET_CHANNEL_ID,
                video=file.file_id,
                caption=f"🎬 {movie_title}\n🔐 Kodi: {movie_code}"
            )
        else:
            sent_msg = await bot.send_document(
                chat_id=Config.SECRET_CHANNEL_ID,
                document=file.file_id,
                caption=f"📄 {movie_title}\n🔐 Kodi: {movie_code}"
            )
        
        await message.answer(
            f"✅ Kino muvaffaqiyatli qo'shildi!\n\n"
            f"📌 Nomi: {movie_title}\n"
            f"🔢 Kodi: {movie_code}\n"
            f"📁 Turi: {'Video' if file_type == 'video' else 'Dokument'}\n\n"
            f"Kino {Config.SECRET_CHANNEL_LINK} kanaliga joylashtirildi."
        )
        
    except Exception as e:
        logger.error(f"Kino qo'shishda xato: {e}")
        await message.answer("❌ Kino yuklashda xatolik yuz berdi!")
    
    await state.clear()

# Asosiy menyu
@dp.message(F.text == "🏠 Asosiy menyu")
async def main_menu(message: types.Message):
    await start_handler(message)

async def main():
    logger.info("Bot ishga tushmoqda...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
