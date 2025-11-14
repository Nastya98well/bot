import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
ADMIN_IDS = [1103762169, 1022006700, 236790169, 213995035]
MAX_USERS = 10

# Временное хранилище данных пользователей
user_sessions = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    
    if len(user_sessions) >= MAX_USERS:
        await update.message.reply_text('⚠️ Сейчас много активных пользователей. Попробуйте через 5-10 минут.')
        return
    
    user_sessions[chat_id] = {'step': 'child_name'}
    
    await update.message.reply_text(
        'Привет! Рада вашему интересу к проекту 💛\n'
        'Участие в портфолио — 17000 ₽. Оставьте данные в анкете, и мы свяжемся после рассмотрения заявки🌠\n\n'
        '👶 *Шаг 1 из 8:* Введите имя ребенка',
        parse_mode='Markdown'
    )

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id

    if chat_id not in user_sessions:
        await update.message.reply_text('Пожалуйста, начните с команды /start')
        return

    session = user_sessions[chat_id]

    if session['step'] == 'photo':
        try:
            photo_file = await update.message.photo[-1].get_file()
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            photo_filename = f"{chat_id}_{timestamp}.jpg"
            
            await photo_file.download_to_drive(photo_filename)
            
            session['photo_path'] = photo_filename
            session['step'] = 'video'
            
            await update.message.reply_text(
                '✅ Фото сохранено!\n\n🎥 *Шаг 3 из 8:* Отправьте видео ребенка (до 1 минуты)',
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Error saving photo: {e}")
            await update.message.reply_text('❌ Ошибка при сохранении фото. Попробуйте еще раз.')

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id

    if chat_id not in user_sessions:
        await update.message.reply_text('Пожалуйста, начните с команды /start')
        return

    session = user_sessions[chat_id]

    if session['step'] == 'video':
        try:
            video = update.message.video
            
            if video.duration > 60:
                await update.message.reply_text('❌ Видео слишком длинное! Пожалуйста, отправьте видео до 1 минуты.')
                return
            
            video_file = await video.get_file()
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            video_filename = f"{chat_id}_{timestamp}.mp4"
            
            await video_file.download_to_drive(video_filename)
            
            session['video_path'] = video_filename
            session['step'] = 'foot_size'
            
            await update.message.reply_text(
                '✅ Видео сохранено!\n\n👣 *Шаг 4 из 8:* Введите размер ноги ребенка (в см)',
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Error saving video: {e}")
            await update.message.reply_text('❌ Ошибка при сохранении видео. Попробуйте еще раз.')

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    text = update.message.text.strip()

    if chat_id not in user_sessions:
        await update.message.reply_text('Пожалуйста, начните с команды /start')
        return

    session = user_sessions[chat_id]

    if session['step'] == 'child_name':
        if len(text) < 2:
            await update.message.reply_text('❌ Пожалуйста, введите имя ребенка')
            return

        session['child_name'] = text
        session['step'] = 'photo'

        await update.message.reply_text(
            '✅ Имя ребенка сохранено!\n\n📸 *Шаг 2 из 8:* Отправьте фотографию ребенка',
            parse_mode='Markdown'
        )

    elif session['step'] == 'foot_size':
        try:
            foot_size = float(text.replace(',', '.'))
            if foot_size <= 0 or foot_size > 30:
                await update.message.reply_text('❌ Пожалуйста, введите корректный размер ноги (0-30 см)')
                return

            session['foot_size'] = text
            session['step'] = 'height'

            await update.message.reply_text(
                '✅ Размер ноги сохранен!\n\n📏 *Шаг 5 из 8:* Введите рост ребенка (в см)',
                parse_mode='Markdown'
            )
        except ValueError:
            await update.message.reply_text('❌ Пожалуйста, введите число для размера ноги')

    elif session['step'] == 'height':
        try:
            height = float(text.replace(',', '.'))
            if height <= 0 or height > 200:
                await update.message.reply_text('❌ Пожалуйста, введите корректный рост (0-200 см)')
                return

            session['height'] = text
            session['step'] = 'parent_name'

            await update.message.reply_text(
                '✅ Рост сохранен!\n\n👤 *Шаг 6 из 8:* Введите ваше имя',
                parse_mode='Markdown'
            )
        except ValueError:
            await update.message.reply_text('❌ Пожалуйста, введите число для роста')

    elif session['step'] == 'parent_name':
        if len(text) < 2:
            await update.message.reply_text('❌ Пожалуйста, введите ваше имя')
            return

        session['parent_name'] = text
        session['step'] = 'parent_phone'

        await update.message.reply_text(
            '✅ Имя сохранено!\n\n📱 *Шаг 7 из 8:* Введите ваш номер телефона',
            parse_mode='Markdown'
        )

    elif session['step'] == 'parent_phone':
        phone = ''.join(filter(str.isdigit, text))
        if len(phone) not in [10, 11]:
            await update.message.reply_text('❌ Пожалуйста, введите корректный номер телефона')
            return

        session['parent_phone'] = phone
        session['step'] = 'parent_telegram'

        await update.message.reply_text(
            '✅ Телефон сохранен!\n\n✈️ *Шаг 8 из 8:* Введите ваш Telegram в формате @username',
            parse_mode='Markdown'
        )

    elif session['step'] == 'parent_telegram':
        if not text.startswith('@'):
            await update.message.reply_text('❌ Пожалуйста, введите username в формате @username')
            return

        session['parent_telegram'] = text
        await save_complete_data(chat_id, update, context)

async def save_complete_data(chat_id, update, context: ContextTypes.DEFAULT_TYPE):
    try:
        session = user_sessions[chat_id]
        
        user_data = {
            'chat_id': chat_id,
            'timestamp': datetime.now().isoformat(),
            'child_name': session.get('child_name', ''),
            'photo_path': session.get('photo_path', ''),
            'video_path': session.get('video_path', ''),
            'foot_size': session.get('foot_size', ''),
            'height': session.get('height', ''),
            'parent_name': session.get('parent_name', ''),
            'parent_phone': session.get('parent_phone', ''),
            'parent_telegram': session.get('parent_telegram', ''),
            'date_str': datetime.now().strftime("%d.%m.%Y %H:%M")
        }

        await notify_admins(context, user_data)
        del user_sessions[chat_id]

        await update.message.reply_text('🎉 *Все данные успешно сохранены!*\n\nСпасибо за заявку! Мы свяжемся с вами.', parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Error in save_complete_data: {e}")
        if chat_id in user_sessions:
            del user_sessions[chat_id]
        await update.message.reply_text('✅ Данные сохранены! Спасибо!')

async def notify_admins(context: ContextTypes.DEFAULT_TYPE, user_data: dict):
    message = (
        "📦 *Новая заявка:*\n\n"
        f"👶 *Ребенок:* {user_data['child_name']}\n"
        f"👣 *Размер ноги:* {user_data['foot_size']} см\n"
        f"📏 *Рост:* {user_data['height']} см\n"
        f"👤 *Родитель:* {user_data['parent_name']}\n"
        f"📱 *Телефон:* {user_data['parent_phone']}\n"
        f"✈️ *Telegram:* {user_data['parent_telegram']}\n"
        f"🕒 *Время:* {user_data['date_str']}"
    )

    for admin_id in ADMIN_IDS:
        try:
            if user_data.get('photo_path') and os.path.exists(user_data['photo_path']):
                with open(user_data['photo_path'], 'rb') as photo:
                    await context.bot.send_photo(
                        chat_id=admin_id,
                        photo=photo,
                        caption=message,
                        parse_mode='Markdown'
                    )
            else:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=message,
                    parse_mode='Markdown'
                )

            if user_data.get('video_path') and os.path.exists(user_data['video_path']):
                with open(user_data['video_path'], 'rb') as video:
                    await context.bot.send_video(
                        chat_id=admin_id,
                        video=video,
                        caption=f"🎥 Видео: {user_data['child_name']}",
                        supports_streaming=True
                    )

        except Exception as e:
            logger.error(f"Ошибка отправки админу {admin_id}: {e}")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    if chat_id in user_sessions:
        del user_sessions[chat_id]
    await update.message.reply_text('❌ Заявка отменена. Чтобы начать заново, используйте /start')

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if user_id not in ADMIN_IDS:
        await update.message.reply_text('❌ Эта команда доступна только администраторам')
        return

    await update.message.reply_text(
        f'📊 *Статистика:*\n• Активных сессий: {len(user_sessions)}',
        parse_mode='Markdown'
    )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Exception while handling an update: {context.error}")

def main():
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("cancel", cancel))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.VIDEO, handle_video))
    application.add_error_handler(error_handler)

    logger.info("Бот запускается на Render...")
    application.run_polling()

if __name__ == '__main__':
    main()
