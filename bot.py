import os
import logging
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ============================================
# ВЕБ-СЕРВЕР ДЛЯ RENDER.COM
# ============================================

app = Flask(__name__)

@app.route('/')
def home():
    return f"""
    <html>
        <body style="font-family: Arial; padding: 20px;">
            <h1>✅ Telegram Bot Status</h1>
            <p>Bot is running!</p>
            <hr>
            <p>Prefix: {PREFIX_TEXT}</p>
        </body>
    </html>
    """

@app.route('/health')
def health():
    return "OK", 200

def run_web():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

# ============================================
# НАСТРОЙКИ БОТА
# ============================================

BOT_TOKEN = os.environ.get('BOT_TOKEN')
if not BOT_TOKEN:
    print("❌ ОШИБКА: BOT_TOKEN не найден!")
    print("Добавьте BOT_TOKEN в Environment Variables на Render.com")
    exit(1)

PREFIX_TEXT = os.environ.get('PREFIX_TEXT', 'Хеллоу')
current_prefix = PREFIX_TEXT

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ============================================
# ОБРАБОТЧИКИ КОМАНД
# ============================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    global current_prefix
    
    user = update.effective_user
    await update.message.reply_text(
        f"👋 Привет, {user.first_name}!\n\n"
        f"Я бот, который добавляет префикс к твоим сообщениям.\n\n"
        f"📝 Текущий префикс: «{current_prefix}»\n\n"
        f"Отправь мне любое сообщение, и я отправлю его обратно с префиксом!\n\n"
        f"Команды:\n"
        f"/start - это сообщение\n"
        f"/setprefix <текст> - изменить префикс\n"
        f"/prefix - показать текущий префикс"
    )
    logger.info(f"Новый пользователь: {user.username or user.id}")

async def show_prefix(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает текущий префикс"""
    global current_prefix
    await update.message.reply_text(
        f"📝 Текущий префикс: «{current_prefix}»"
    )

async def set_prefix(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Изменяет префикс"""
    global current_prefix
    
    # Получаем новый префикс из аргументов команды
    if context.args:
        new_prefix = ' '.join(context.args)
        current_prefix = new_prefix
        await update.message.reply_text(
            f"✅ Префикс изменен на: «{current_prefix}»"
        )
        logger.info(f"Префикс изменен на: {current_prefix}")
    else:
        await update.message.reply_text(
            "❌ Укажите новый префикс после команды.\n"
            "Пример: /setprefix Новый текст"
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик всех сообщений"""
    global current_prefix
    
    message = update.message
    
    # Добавляем префикс к тексту
    original_text = message.caption or message.text or ""
    new_text = f"{current_prefix}\n\n{original_text}" if original_text else current_prefix
    
    try:
        # Обработка фото
        if message.photo:
            await message.reply_photo(
                photo=message.photo[-1].file_id,
                caption=new_text
            )
            logger.info("Обработано фото")
            
        # Обработка видео
        elif message.video:
            await message.reply_video(
                video=message.video.file_id,
                caption=new_text
            )
            logger.info("Обработано видео")
            
        # Обработка документов
        elif message.document:
            await message.reply_document(
                document=message.document.file_id,
                caption=new_text
            )
            logger.info("Обработан документ")
            
        # Обработка аудио
        elif message.audio:
            await message.reply_audio(
                audio=message.audio.file_id,
                caption=new_text
            )
            logger.info("Обработано аудио")
            
        # Обработка голосовых
        elif message.voice:
            await message.reply_voice(
                voice=message.voice.file_id
            )
            await message.reply_text(new_text)
            logger.info("Обработано голосовое")
            
        # Обработка видео-заметок
        elif message.video_note:
            await message.reply_video_note(
                video_note=message.video_note.file_id
            )
            await message.reply_text(new_text)
            logger.info("Обработана видео-заметка")
            
        # Обработка стикеров
        elif message.sticker:
            await message.reply_sticker(
                sticker=message.sticker.file_id
            )
            if new_text:
                await message.reply_text(new_text)
            logger.info("Обработан стикер")
            
        # Обработка локаций
        elif message.location:
            await message.reply_location(
                latitude=message.location.latitude,
                longitude=message.location.longitude
            )
            if new_text:
                await message.reply_text(new_text)
            logger.info("Обработана локация")
            
        # Обработка контактов
        elif message.contact:
            await message.reply_contact(
                phone_number=message.contact.phone_number,
                first_name=message.contact.first_name,
                last_name=message.contact.last_name or ""
            )
            if new_text:
                await message.reply_text(new_text)
            logger.info("Обработан контакт")
            
        # Обработка текста
        elif message.text:
            await message.reply_text(new_text)
            logger.info("Обработан текст")
            
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await message.reply_text(
            "❌ Произошла ошибка при обработке сообщения."
        )

def main():
    """Главная функция"""
    
    logger.info("=" * 50)
    logger.info(f"🤖 Бот запускается...")
    logger.info(f"📝 Префикс: «{current_prefix}»")
    logger.info("=" * 50)
    
    # Запускаем веб-сервер
    web_thread = Thread(target=run_web, daemon=True)
    web_thread.start()
    logger.info("✅ Веб-сервер запущен")
    
    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Регистрируем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("prefix", show_prefix))
    application.add_handler(CommandHandler("setprefix", set_prefix))
    
    # Обработчик всех остальных сообщений
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))
    
    # Запускаем бота
    logger.info("✅ Бот готов к работе!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()