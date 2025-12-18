import os
import logging
from typing import Dict
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Хранение данных (временное, для демо)
user_data = {}

class ReferralBot:
    def __init__(self):
        self.token = os.getenv("BOT_TOKEN")
        if not self.token:
            raise ValueError("BOT_TOKEN not found in environment variables")
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        user = update.effective_user
        referral_code = None
        
        if context.args:
            referral_code = context.args[0]
        
        if user.id not in user_data:
            user_data[user.id] = {
                'referrer_id': int(referral_code) if referral_code and referral_code.isdigit() else None,
                'balance': 0,
                'referrals': [],
                'username': user.username
            }
            
            if referral_code and referral_code.isdigit():
                referrer_id = int(referral_code)
                if referrer_id in user_data:
                    user_data[referrer_id]['referrals'].append(user.id)
                    user_data[referrer_id]['balance'] += 10
                    
                    try:
                        await context.bot.send_message(
                            chat_id=referrer_id,
                            text=f"🎉 У вас новый реферал! @{user.username if user.username else 'Пользователь'}"
                        )
                    except:
                        pass
        
        keyboard = [
            [InlineKeyboardButton("👥 Мои рефералы", callback_data='my_referrals')],
            [InlineKeyboardButton("💰 Баланс", callback_data='balance')],
            [InlineKeyboardButton("📢 Поделиться ссылкой", callback_data='share')],
            [InlineKeyboardButton("ℹ️ Помощь", callback_data='help')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        ref_link = f"https://t.me/{context.bot.username}?start={user.id}"
        
        await update.message.reply_text(
            f"👋 Привет, {user.first_name}!\n\n"
            f"🎁 <b>Реферальная система:</b>\n"
            f"• За каждого приглашенного друга: <b>10 монет</b>\n"
            f"• Друг получает: <b>5 монет</b> на старт\n\n"
            f"🔗 <b>Ваша реферальная ссылка:</b>\n"
            f"<code>{ref_link}</code>\n\n"
            f"📊 <b>Статистика:</b>\n"
            f"• Ваши рефералы: {len(user_data[user.id]['referrals'])}\n"
            f"• Баланс: {user_data[user.id]['balance']} монет",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    
    async def balance_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        if user.id in user_data:
            await update.message.reply_text(
                f"💰 Ваш баланс: {user_data[user.id]['balance']} монет\n"
                f"👥 Рефералов: {len(user_data[user.id]['referrals'])}"
            )
        else:
            await update.message.reply_text("Сначала используйте /start")
    
    async def referrals_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        if user.id in user_data:
            referrals = user_data[user.id]['referrals']
            if referrals:
                ref_list = "\n".join([f"• @{user_data.get(ref_id, {}).get('username', 'Пользователь')}" 
                                    for ref_id in referrals[:20]])
                await update.message.reply_text(
                    f"👥 Ваши рефералы ({len(referrals)}):\n{ref_list}"
                )
            else:
                await update.message.reply_text("У вас пока нет рефералов 😢")
        else:
            await update.message.reply_text("Сначала используйте /start")
    
    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        user = query.from_user
        
        if query.data == 'my_referrals':
            if user.id in user_data:
                referrals = user_data[user.id]['referrals']
                if referrals:
                    ref_list = "\n".join([f"• @{user_data.get(ref_id, {}).get('username', 'Пользователь')}" 
                                        for ref_id in referrals[:10]])
                    await query.edit_message_text(
                        text=f"👥 Ваши рефералы ({len(referrals)}):\n{ref_list}"
                    )
                else:
                    await query.edit_message_text(text="У вас пока нет рефералов 😢")
        
        elif query.data == 'balance':
            if user.id in user_data:
                await query.edit_message_text(
                    text=f"💰 Баланс: {user_data[user.id]['balance']} монет\n"
                         f"👥 Рефералов: {len(user_data[user.id]['referrals'])}"
                )
        
        elif query.data == 'share':
            ref_link = f"https://t.me/{context.bot.username}?start={user.id}"
            await query.edit_message_text(
                text=f"📢 <b>Приглашайте друзей и получайте бонусы!</b>\n\n"
                     f"🔗 <b>Ваша реферальная ссылка:</b>\n"
                     f"<code>{ref_link}</code>\n\n"
                     f"🎁 <b>Бонусы:</b>\n"
                     f"• Вы получаете: 10 монет за друга\n"
                     f"• Друг получает: 5 монет на старт",
                parse_mode='HTML'
            )
        
        elif query.data == 'help':
            await query.edit_message_text(
                text="ℹ️ <b>Как работает бот:</b>\n\n"
                     "1. Поделитесь своей реферальной ссылкой с друзьями\n"
                     "2. Когда друг перейдет по вашей ссылке и нажмет START\n"
                     "3. Вы получите 10 монет на баланс\n"
                     "4. Ваш друг получит 5 монет на старт\n\n"
                     "<b>Команды:</b>\n"
                     "/start - Запустить бота\n"
                     "/balance - Проверить баланс\n"
                     "/referrals - Мои рефералы\n"
                     "/help - Помощь",
                parse_mode='HTML'
            )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "ℹ️ <b>Помощь по боту:</b>\n\n"
            "🎁 <b>Реферальная система:</b>\n"
            "1. Получите свою реферальную ссылку\n"
            "2. Поделитесь с друзьями\n"
            "3. Получайте бонусы за каждого приглашенного!\n\n"
            "<b>Доступные команды:</b>\n"
            "/start - Запустить бота\n"
            "/balance - Проверить баланс\n"
            "/referrals - Мои рефералы\n"
            "/help - Помощь",
            parse_mode='HTML'
        )
    
    def run(self):
        application = Application.builder().token(self.token).build()
        
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(CommandHandler("balance", self.balance_command))
        application.add_handler(CommandHandler("referrals", self.referrals_command))
        application.add_handler(CommandHandler("help", self.help_command))
        application.add_handler(CallbackQueryHandler(self.button_handler))
        
        print("🤖 Бот запущен...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    bot = ReferralBot()
    bot.run()
