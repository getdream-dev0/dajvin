import asyncio
import logging
import os
from typing import Optional
from flask import Flask
from threading import Thread
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InputMediaPhoto, InputMediaVideo, InputMediaDocument, InputMediaAudio

# ============================================
# ВЕБ-СЕРВЕР ДЛЯ RENDER.COM
# Render требует веб-сервер на определенном порту
# чтобы понимать что приложение живое
# ============================================

app = Flask(__name__)

@app.route('/')
def home():
    """Главная страница - показывает статус бота"""
    return """
    <html>
        <body style="font-family: Arial; padding: 20px;">
            <h1>✅ Telegram Bot Status</h1>
            <p>Bot is running!</p>
            <hr>
            <p>Prefix: """ + PREFIX_TEXT + """</p>
            <p>Send /start to your bot in Telegram to begin</p>
        </body>
    </html>
    """

@app.route('/health')
def health():
    """Endpoint для проверки здоровья приложения"""
    return "OK", 200

def run_web_server():
    """Запуск Flask сервера"""
    port = int(os.environ.get('PORT', 8080))
    print(f"Starting web server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)

# ============================================
# НАСТРОЙКИ БОТА
# ============================================

# Получаем токен из переменных окружения Render
BOT_TOKEN = os.environ.get('BOT_TOKEN')
if not BOT_TOKEN:
    print("❌ ОШИБКА: BOT_TOKEN не найден!")
    print("Добавьте BOT_TOKEN в Environment Variables на Render.com")
    print("Инструкция:")
    print("1. Откройте настройки вашего сервиса на Render")
    print("2. Перейдите в Environment")
    print("3. Добавьте переменную BOT_TOKEN со значением токена от @BotFather")
    exit(1)

# Префикс по умолчанию (можно изменить через переменную окружения)
PREFIX_TEXT = os.environ.get('PREFIX_TEXT', 'Хеллоу')

# ============================================
# НАСТРОЙКА ЛОГИРОВАНИЯ
# ============================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================
# ИНИЦИАЛИЗАЦИЯ БОТА
# ============================================

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Глобальная переменная для хранения префикса (можно менять командой)
current_prefix = PREFIX_TEXT

# ============================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================

def add_prefix_to_text(text: Optional[str]) -> str:
    """Добавляет префикс к тексту сообщения"""
    global current_prefix
    if text:
        return f"{current_prefix}\n\n{text}"
    return current_prefix

# ============================================
# ОБРАБОТЧИКИ КОМАНД
# ============================================

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Приветственное сообщение при команде /start"""
    global current_prefix
    
    welcome_text = f"""
👋 <b>Привет, {message.from_user.first_name}!</b>

Я бот, который добавляет префикс к твоим сообщениям.

📝 <b>Текущий префикс:</b> «{current_prefix}»

<b>Как я работаю:</b>
• Отправь мне любое сообщение (текст, фото, видео, документ)
• Я отправлю его обратно с добавленным префиксом

<b>Команды:</b>
/start - это сообщение
/setprefix <текст> - изменить префикс
/prefix - показать текущий префикс
/help - помощь

<b>Примеры:</b>
• Ты: "Привет"
• Я: "{current_prefix}

Привет"

Попробуй отправить мне что-нибудь! 🚀
"""
    
    await message.answer(welcome_text, parse_mode="HTML")
    logger.info(f"Новый пользователь: {message.from_user.username or message.from_user.id}")

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    """Справка по использованию бота"""
    global current_prefix
    
    help_text = f"""
📖 <b>Справка по боту</b>

<b>Поддерживаемые типы сообщений:</b>
✅ Текст
✅ Фото (одиночные и альбомы)
✅ Видео
✅ Документы
✅ Аудио
✅ Голосовые сообщения
✅ Стикеры
✅ Локации
✅ Контакты

<b>Команды:</b>
• /start - начать работу
• /setprefix Новый текст - изменить префикс
• /prefix - показать текущий префикс
• /help - эта справка

<b>Текущий префикс:</b> «{current_prefix}»

<b>Статус бота:</b> ✅ Работает на Render.com
"""
    
    await message.answer(help_text, parse_mode="HTML")

@dp.message(Command("prefix"))
async def cmd_prefix(message: types.Message):
    """Показывает текущий префикс"""
    global current_prefix
    await message.answer(
        f"📝 Текущий префикс: «{current_prefix}»\n\n"
        f"Чтобы изменить, используйте:\n"
        f"/setprefix Новый текст"
    )

@dp.message(Command("setprefix"))
async def cmd_setprefix(message: types.Message):
    """Изменяет префикс"""
    global current_prefix
    
    # Извлекаем новый префикс из команды
    command_parts = message.text.split(maxsplit=1)
    
    if len(command_parts) > 1:
        new_prefix = command_parts[1]
        current_prefix = new_prefix
        
        await message.answer(
            f"✅ <b>Префикс успешно изменен!</b>\n\n"
            f"Новый префикс: «{current_prefix}»\n\n"
            f"Попробуйте отправить любое сообщение, чтобы увидеть результат.",
            parse_mode="HTML"
        )
        
        logger.info(f"Префикс изменен на: {current_prefix}")
    else:
        await message.answer(
            "❌ <b>Ошибка!</b>\n\n"
            "Укажите новый префикс после команды.\n\n"
            "<b>Пример:</b>\n"
            "/setprefix Добрый день",
            parse_mode="HTML"
        )

# ============================================
# ОБРАБОТЧИК ВСЕХ СООБЩЕНИЙ
# ============================================

# Словарь для хранения медиа-групп (альбомов)
media_groups = {}

@dp.message()
async def handle_message(message: types.Message):
    """Обрабатывает все входящие сообщения и добавляет префикс"""
    
    try:
        # Получаем текст (caption для медиа или text для обычных сообщений)
        original_text = message.caption or message.text or ""
        new_text = add_prefix_to_text(original_text)
        
        # === МЕДИА-ГРУППЫ (АЛЬБОМЫ) ===
        if message.media_group_id:
            await handle_media_group(message, new_text)
            return
            
        # === ФОТО ===
        if message.photo:
            await message.answer_photo(
                photo=message.photo[-1].file_id,  # Берем максимальное качество
                caption=new_text
            )
            logger.info("Обработано фото")
            
        # === ВИДЕО ===
        elif message.video:
            await message.answer_video(
                video=message.video.file_id,
                caption=new_text
            )
            logger.info("Обработано видео")
            
        # === ДОКУМЕНТЫ ===
        elif message.document:
            await message.answer_document(
                document=message.document.file_id,
                caption=new_text
            )
            logger.info("Обработан документ")
            
        # === АУДИО ===
        elif message.audio:
            await message.answer_audio(
                audio=message.audio.file_id,
                caption=new_text
            )
            logger.info("Обработано аудио")
            
        # === ГОЛОСОВЫЕ СООБЩЕНИЯ ===
        elif message.voice:
            await message.answer_voice(
                voice=message.voice.file_id,
                caption=new_text if new_text != current_prefix else None
            )
            if new_text == current_prefix:
                await message.answer(new_text)
            logger.info("Обработано голосовое")
            
        # === ВИДЕО-ЗАМЕТКИ (КРУЖОЧКИ) ===
        elif message.video_note:
            await message.answer_video_note(
                video_note=message.video_note.file_id
            )
            # Кружочки не поддерживают caption
            await message.answer(new_text)
            logger.info("Обработана видео-заметка")
            
        # === СТИКЕРЫ ===
        elif message.sticker:
            await message.answer_sticker(
                sticker=message.sticker.file_id
            )
            # Стикеры не поддерживают caption
            if new_text:
                await message.answer(new_text)
            logger.info("Обработан стикер")
            
        # === ЛОКАЦИИ ===
        elif message.location:
            await message.answer_location(
                latitude=message.location.latitude,
                longitude=message.location.longitude
            )
            if new_text:
                await message.answer(new_text)
            logger.info("Обработана локация")
            
        # === КОНТАКТЫ ===
        elif message.contact:
            await message.answer_contact(
                phone_number=message.contact.phone_number,
                first_name=message.contact.first_name,
                last_name=message.contact.last_name or "",
                vcard=message.contact.vcard
            )
            if new_text:
                await message.answer(new_text)
            logger.info("Обработан контакт")
            
        # === ОБЫЧНЫЙ ТЕКСТ ===
        elif message.text:
            await message.answer(new_text)
            logger.info("Обработан текст")
        
    except Exception as e:
        logger.error(f"Ошибка при обработке сообщения: {e}")
        await message.answer(
            "❌ Произошла ошибка при обработке сообщения.\n"
            "Попробуйте еще раз или обратитесь к администратору."
        )

async def handle_media_group(message: types.Message, new_text: str):
    """Обработка альбомов (несколько фото/видео в одном сообщении)"""
    
    media_group_id = message.media_group_id
    
    # Создаем запись для новой группы
    if media_group_id not in media_groups:
        media_groups[media_group_id] = {
            'messages': [],
            'user_id': message.from_user.id,
            'chat_id': message.chat.id,
            'timer': None
        }
    
    group = media_groups[media_group_id]
    group['messages'].append(message)
    
    # Отменяем предыдущий таймер если есть
    if group['timer']:
        group['timer'].cancel()
    
    # Функция для отправки альбома
    async def send_album():
        if media_group_id not in media_groups:
            return
            
        group_data = media_groups[media_group_id]
        media_list = []
        
        # Собираем все медиа из группы
        for idx, msg in enumerate(group_data['messages']):
            # Добавляем caption только к первому элементу
            caption = new_text if idx == 0 else None
            
            if msg.photo:
                media = InputMediaPhoto(
                    media=msg.photo[-1].file_id,
                    caption=caption
                )
            elif msg.video:
                media = InputMediaVideo(
                    media=msg.video.file_id,
                    caption=caption
                )
            elif msg.document:
                media = InputMediaDocument(
                    media=msg.document.file_id,
                    caption=caption
                )
            elif msg.audio:
                media = InputMediaAudio(
                    media=msg.audio.file_id,
                    caption=caption
                )
            else:
                continue
                
            media_list.append(media)
        
        # Отправляем альбом
        if media_list:
            try:
                await bot.send_media_group(
                    chat_id=group_data['chat_id'],
                    media=media_list
                )
                logger.info(f"Отправлен альбом из {len(media_list)} элементов")
            except Exception as e:
                logger.error(f"Ошибка отправки альбома: {e}")
        
        # Удаляем группу из памяти
        if media_group_id in media_groups:
            del media_groups[media_group_id]
    
    # Запускаем таймер на 1 секунду
    # Если за это время придут еще медиа - таймер перезапустится
    loop = asyncio.get_event_loop()
    group['timer'] = loop.call_later(1.0, lambda: asyncio.create_task(send_album()))

# ============================================
# ГЛАВНАЯ ФУНКЦИЯ
# ============================================

async def main():
    """Основная функция запуска бота"""
    
    logger.info("=" * 50)
    logger.info(f"🤖 Бот запускается...")
    logger.info(f"📝 Префикс: «{current_prefix}»")
    logger.info(f"🌐 Платформа: Render.com")
    logger.info("=" * 50)
    
    # Запускаем веб-сервер в отдельном потоке
    web_thread = Thread(target=run_web_server, daemon=True)
    web_thread.start()
    logger.info("✅ Веб-сервер запущен")
    
    # Удаляем старые вебхуки если есть
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("✅ Вебхуки очищены")
    
    # Запускаем polling
    logger.info("✅ Бот готов к работе!")
    logger.info("Отправьте /start боту в Telegram")
    
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Ошибка polling: {e}")

# ============================================
# ТОЧКА ВХОДА
# ============================================

if __name__ == "__main__":
    try:
        # Запускаем асинхронную главную функцию
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⏹ Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        exit(1)