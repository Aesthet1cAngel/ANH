import logging
import json
import os
from datetime import datetime
from telegram import Update, ChatPermissions
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackContext

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Файлы для хранения данных
ADMINS_FILE = 'admins.json'
BANNED_FILE = 'banned.json'

# Загружаем данные администраторов
def load_admins():
    if os.path.exists(ADMINS_FILE):
        with open(ADMINS_FILE, 'r') as f:
            return json.load(f)
    return {}

# Загружаем данные забаненных пользователей
def load_banned():
    if os.path.exists(BANNED_FILE):
        with open(BANNED_FILE, 'r') as f:
            return json.load(f)
    return {}

# Сохраняем данные администраторов
def save_admins(admins):
    with open(ADMINS_FILE, 'w') as f:
        json.dump(admins, f, indent=4)

# Сохраняем данные забаненных пользователей
def save_banned(banned):
    with open(BANNED_FILE, 'w') as f:
        json.dump(banned, f, indent=4)

# Проверка, является ли пользователь администратором
def is_admin(user_id: int) -> bool:
    admins = load_admins()
    return str(user_id) in admins

# Проверка, забанен ли пользователь
def is_banned(user_id: int) -> bool:
    banned = load_banned()
    return str(user_id) in banned

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    # Проверяем, не забанен ли пользователь
    if is_banned(user.id):
        await update.message.reply_text("🚫 Вы забанены и не можете использовать бота.")
        return
    
    await update.message.reply_text(
        f"👋 Привет, {user.first_name}!\n"
        "Я чат-бот для общения с системой модерации.\n"
        "Используйте /help для списка команд."
    )

# Команда /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    
    if is_admin(user_id):
        help_text = (
            "📚 Команды для всех:\n"
            "/start - начать работу\n"
            "/help - показать справку\n"
            "/rules - правила чата\n"
            "/online - кто онлайн\n\n"
            "⚡ Команды администратора:\n"
            "/admin [user_id] - добавить админа\n"
            "/unadmin [user_id] - удалить админа\n"
            "/ban [reply] - забанить пользователя\n"
            "/unban [user_id] - разбанить пользователя\n"
            "/list_admins - список администраторов\n"
            "/list_banned - список забаненных\n"
            "/mute [reply] [time] - заглушить пользователя\n"
            "/unmute [reply] - снять заглушку\n"
            "/warn [reply] - выдать предупреждение\n"
            "/kick [reply] - кикнуть пользователя\n"
            "/users - статистика пользователей"
        )
    else:
        help_text = (
            "📚 Доступные команды:\n"
            "/start - начать работу\n"
            "/help - показать эту справку\n"
            "/rules - правила чата\n"
            "/online - кто онлайн\n\n"
            "Просто пишите сообщения в чат, и все участники их увидят!"
        )
    
    await update.message.reply_text(help_text)

# Команда /rules
async def rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rules_text = (
        "📝 Правила чата:\n"
        "1. Уважайте друг друга\n"
        "2. Не спамьте\n"
        "3. Не нарушайте законы\n"
        "4. Будьте вежливы\n"
        "5. Запрещена реклама без разрешения\n"
        "6. Не флудите\n"
        "7. Слушайтесь администраторов\n\n"
        "⚠️ Нарушение правил ведет к варну, муту, бану или кику!"
    )
    await update.message.reply_text(rules_text)
# Команда /admin - сделать пользователя администратором
async def make_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    # Проверяем права текущего пользователя
    if not is_admin(user.id):
        await update.message.reply_text("❌ У вас нет прав для выполнения этой команды.")
        return
    
    # Проверяем, указан ли user_id
    if not context.args:
        await update.message.reply_text("❌ Использование: /admin [user_id]")
        return
    
    try:
        target_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ Неверный формат user_id.")
        return
    
    # Загружаем и обновляем список администраторов
    admins = load_admins()
    admins[str(target_id)] = {
        'added_by': user.id,
        'added_at': datetime.now().isoformat(),
        'username': context.args[1] if len(context.args) > 1 else 'unknown'
    }
    save_admins(admins)
    
    await update.message.reply_text(f"✅ Пользователь {target_id} добавлен в администраторы.")

# Команда /unadmin - удалить администратора
async def remove_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    if not is_admin(user.id):
        await update.message.reply_text("❌ У вас нет прав для выполнения этой команды.")
        return
    
    if not context.args:
        await update.message.reply_text("❌ Использование: /unadmin [user_id]")
        return
    
    try:
        target_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ Неверный формат user_id.")
        return
    
    # Проверяем, не пытаемся ли удалить себя
    if target_id == user.id:
        await update.message.reply_text("❌ Вы не можете удалить себя из администраторов.")
        return
    
    admins = load_admins()
    if str(target_id) in admins:
        del admins[str(target_id)]
        save_admins(admins)
        await update.message.reply_text(f"✅ Пользователь {target_id} удален из администраторов.")
    else:
        await update.message.reply_text(f"❌ Пользователь {target_id} не найден в списке администраторов.")

# Команда /list_admins - список администраторов
async def list_admins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    if not is_admin(user.id):
        await update.message.reply_text("❌ У вас нет прав для выполнения этой команды.")
        return
    
    admins = load_admins()
    if not admins:
        await update.message.reply_text("📋 Список администраторов пуст.")
        return
    
    admin_list = "📋 Список администраторов:\n"
    for admin_id, info in admins.items():
        admin_list += f"👤 ID: {admin_id}\n"
        if 'added_at' in info:
            admin_list += f"   Добавлен: {info['added_at'][:10]}\n"
        admin_list += "\n"
    
    await update.message.reply_text(admin_list)

# Команда /ban - забанить пользователя
async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    if not is_admin(user.id):
        await update.message.reply_text("❌ У вас нет прав для выполнения этой команды.")
        return
    
    # Проверяем, отвечает ли команда на сообщение
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ Ответьте на сообщение пользователя, которого хотите забанить.")
        return
    
    target_user = update.message.reply_to_message.from_user
    target_id = target_user.id
    
    # Проверяем, не пытаемся ли забанить администратора
    if is_admin(target_id):
        await update.message.reply_text("❌ Нельзя забанить администратора.")
        return
    
    # Проверяем, не пытаемся ли забанить себя
    if target_id == user.id:
        await update.message.reply_text("❌ Вы не можете забанить себя.")
        return
    
    # Получаем причину бана
    reason = ' '.join(context.args) if context.args else "Нарушение правил чата"
    
    # Загружаем и обновляем список забаненных
    banned = load_banned()
    banned[str(target_id)] = {
        'banned_by': user.id,
        'banned_at': datetime.now().isoformat(),
        'reason': reason,
        'username': target_user.username or target_user.first_name
    }
    save_banned(banned)
    
    # Пытаемся кикнуть пользователя из чата
    try:
        await context.bot.ban_chat_member(
            chat_id=update.effective_chat.id,
            user_id=target_id
        )
        ban_message = f"🚫 Пользователь {target_user.first_name} забанен.\nПричина: {reason}"
    except Exception as e:
        ban_message = f"⚠️ Пользователь {target_user.first_name} добавлен в черный список бота, но не удален из чата.\nОшибка: {str(e)}"
    
    await update.message.reply_text(ban_message)

# Команда /unban - разбанить пользователя
async def unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    if not is_admin(user.id):
        await update.message.reply_text("❌ У вас нет прав для выполнения этой команды.")
        return
    
    if not context.args:
        await update.message.reply_text("❌ Использование: /unban [user_id]")
        return
    
    try:
        target_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ Неверный формат user_id.")
        return
    
    banned = load_banned()
    if str(target_id) in banned:
        del banned[str(target_id)]
        save_banned(banned)
        
        # Пытаемся разбанить в чате
        try:
            await context.bot.unban_chat_member(
                chat_id=update.effective_chat.id,
                user_id=target_id
            )
            await update.message.reply_text(f"✅ Пользователь {target_id} разбанен.")
        except Exception as e:
            await update.message.reply_text(f"✅ Пользователь {target_id} удален из черного списка бота.")
    else:
        await update.message.reply_text(f"❌ Пользователь {target_id} не найден в черном списке.")

# Команда /list_banned - список забаненных
async def list_banned(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    if not is_admin(user.id):
        await update.message.reply_text("❌ У вас нет прав для выполнения этой команды.")
        return
    
    banned = load_banned()
    if not banned:
        await update.message.reply_text("📋 Черный список пуст.")
        return
    
    banned_list = "📋 Черный список:\n"
    for user_id, info in banned.items():
        banned_list += f"👤 ID: {user_id}\n"
        banned_list += f"   Имя: {info.get('username', 'Неизвестно')}\n"
        banned_list += f"   Причина: {info.get('reason', 'Не указана')}\n"
        if 'banned_at' in info:
            banned_list += f"   Забанен: {info['banned_at'][:10]}\n"
        banned_list += "\n"
    
    await update.message.reply_text(banned_list)

# Команда /kick - кикнуть пользователя
async def kick_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    if not is_admin(user.id):
        await update.message.reply_text("❌ У вас нет прав для выполнения этой команды.")
        return
    
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ Ответьте на сообщение пользователя, которого хотите кикнуть.")
        return
    
    target_user = update.message.reply_to_message.from_user
    target_id = target_user.id
    
    # Проверяем, не пытаемся ли кикнуть администратора
    if is_admin(target_id):
        await update.message.reply_text("❌ Нельзя кикнуть администратора.")
        return
    
    # Получаем причину
    reason = " ".join(context.args) if context.args else "Нарушение правил"
    
    try:
        await context.bot.ban_chat_member(
            chat_id=update.effective_chat.id,
            user_id=target_id,
            until_date=datetime.now().timestamp() + 60  # Бан на 60 секунд
        )
        await update.message.reply_text(f"👢 Пользователь {target_user.first_name} кикнут.\nПричина: {reason}")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка при кике: {str(e)}")

# Команда /mute - заглушить пользователя
async def mute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    if not is_admin(user.id):
        await update.message.reply_text("❌ У вас нет прав для выполнения этой команды.")
        return
    
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ Ответьте на сообщение пользователя, которого хотите заглушить.")
        return
    
    target_user = update.message.reply_to_message.from_user
    target_id = target_user.id
    
    # Определяем время мута (по умолчанию 1 час)
    mute_time = 3600  # 1 час в секундах
    if context.args:
        try:
            time_arg = int(context.args[0])
            if time_arg <= 0:
                await update.message.reply_text("❌ Время должно быть больше 0.")
                return
            mute_time = time_arg * 3600 if time_arg < 168 else time_arg  # Если меньше 168, считаем как часы
        except ValueError:
            await update.message.reply_text("❌ Неверный формат времени.")
            return
    
    try:
        # Устанавливаем ограничения
        permissions = ChatPermissions(
            can_send_messages=False,
            can_send_media_messages=False,
            can_send_polls=False,
            can_send_other_messages=False,
            can_add_web_page_previews=False,
            can_change_info=False,
            can_invite_users=False,
            can_pin_messages=False
        )
        
        await context.bot.restrict_chat_member(
            chat_id=update.effective_chat.id,
            user_id=target_id,
            permissions=permissions,
            until_date=datetime.now().timestamp() + mute_time
        )
        
        time_text = f"{mute_time//3600} часов" if mute_time >= 3600 else f"{mute_time//60} минут"
        await update.message.reply_text(f"🔇 Пользователь {target_user.first_name} заглушен на {time_text}.")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка при муте: {str(e)}")

# Команда /unmute - снять заглушку
async def unmute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    if not is_admin(user.id):
        await update.message.reply_text("❌ У вас нет прав для выполнения этой команды.")
        return
    
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ Ответьте на сообщение пользователя, которого хотите размутить.")
        return
    
    target_user = update.message.reply_to_message.from_user
    target_id = target_user.id
    
    try:
        # Восстанавливаем все разрешения
        permissions = ChatPermissions(
            can_send_messages=True,
            can_send_media_messages=True,
            can_send_polls=True,
            can_send_other_messages=True,
            can_add_web_page_previews=True,
            can_change_info=False,
            can_invite_users=False,
            can_pin_messages=False
        )
        
        await context.bot.restrict_chat_member(
            chat_id=update.effective_chat.id,
            user_id=target_id,
            permissions=permissions
        )
        
        await update.message.reply_text(f"🔊 Пользователь {target_user.first_name} размучен.")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка при размуте: {str(e)}")
# Команда /online - кто онлайн
async def online_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        chat_id = update.effective_chat.id
        # Получаем список администраторов чата
        chat_admins = await context.bot.get_chat_administrators(chat_id)
        
        online_list = "👥 Активные пользователи:\n"
        for member in chat_admins:
            if member.user.is_bot:
                continue
            status = "🟢" if member.user.status == 'online' else "⚫"
            online_list += f"{status} {member.user.first_name}"
            if member.user.username:
                online_list += f" (@{member.user.username})"
            online_list += "\n"
        
        await update.message.reply_text(online_list)
    except Exception as e:
        await update.message.reply_text(f"❌ Не удалось получить список пользователей: {str(e)}")

# Команда /users - статистика
async def users_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    if not is_admin(user.id):
        await update.message.reply_text("❌ У вас нет прав для выполнения этой команды.")
        return
    
    admins = load_admins()
    banned = load_banned()
    
    stats = (
        f"📊 Статистика бота:\n"
        f"👑 Администраторов: {len(admins)}\n"
        f"🚫 Забанено: {len(banned)}\n"
        f"🟢 Вы: {user.first_name} (ID: {user.id})"
    )
    
    await update.message.reply_text(stats)

# Фильтр сообщений - проверяем, не забанен ли отправитель
async def message_filter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    # Проверяем, не забанен ли пользователь
    if is_banned(user.id):
        # Удаляем сообщение забаненного пользователя
        try:
            await update.message.delete()
        except:
            pass
        return
    
    # Если пользователь не забанен, обрабатываем сообщение
    await echo(update, context)

# Обработка обычных сообщений
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message_text = update.message.text
    
    # Форматируем сообщение
    if is_admin(user.id):
        formatted_message = f"👑 {user.first_name}: {message_text}"
    else:
        formatted_message = f"👤 {user.first_name}: {message_text}"
    
    await update.message.reply_text(formatted_message)

# Обработка ошибок
async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.warning(f'Update {update} caused error {context.error}')

# Инициализация данных при запуске
def init_data():
    # Создаем файлы, если они не существуют
    if not os.path.exists(ADMINS_FILE):
        save_admins({})
    if not os.path.exists(BANNED_FILE):
        save_banned({})

def main():
    # Инициализируем данные
    init_data()
    
    # Вставьте сюда ваш токен от BotFather
    TOKEN = "8585057827:AAGZwxHoH90O_7RfdWLGppgcFwssRNK2j4Q"
    
    # Создаем приложение
    application = Application.builder().token(TOKEN).build()
    
    # Регистрируем обработчики команд для всех пользователей
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("rules", rules))
    application.add_handler(CommandHandler("online", online_users))
    
    # Регистрируем обработчики команд для администраторов
    application.add_handler(CommandHandler("admin", make_admin))
    application.add_handler(CommandHandler("unadmin", remove_admin))
    application.add_handler(CommandHandler("list_admins", list_admins))
    application.add_handler(CommandHandler("ban", ban_user))
    application.add_handler(CommandHandler("unban", unban_user))
    application.add_handler(CommandHandler("list_banned", list_banned))
    application.add_handler(CommandHandler("kick", kick_user))
    application.add_handler(CommandHandler("mute", mute_user))
    application.add_handler(CommandHandler("unmute", unmute_user))
    application.add_handler(CommandHandler("users", users_stats))
    
    # Регистрируем обработчик текстовых сообщений с фильтром
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_filter))
    
    # Регистрируем обработчик ошибок
    application.add_error_handler(error)
    
    # Запускаем бота
    print("🤖 Бот с системой модерации запущен...")
    print("⚡ Для добавления первого администратора используйте команду /admin [ваш_id] в ЛС с ботом")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()