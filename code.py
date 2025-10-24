import logging
import sqlite3
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Вставьте сюда токен вашего бота
BOT_TOKEN = "что думали покажу вам токен бота?))" # в будущем надо сделать это в . env скрыто

# Список администраторов (username без @)
ADMINS = ["makarburnashev", "work_man02"]

# Тексты для настройки
WELCOME_TEXT = "Привет! Я помогу тебе найти компанию для учебы. Создавай рабочее место или находи студентов в локации, которые тоже ищут компанию"  # Замените на ваш текст приветствия

# Инициализация базы данных
def init_db():
    conn = sqlite3.connect('hse_students.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            campus TEXT,
            education_level TEXT,
            course INTEGER,
            program_name TEXT,
            program_code TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Таблица для рабочих мест
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS workplaces (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            location TEXT,
            classroom TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')
    
    # Таблица для заблокированных пользователей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS banned_users (
            user_id INTEGER PRIMARY KEY,
            banned_by TEXT,
            ban_reason TEXT,
            banned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

# Функция проверки прав администратора
def is_admin(user):
    username = user.username
    if username:
        return username.lower() in [admin.lower() for admin in ADMINS]
    return False

# Функция проверки бана пользователя
def is_user_banned(user_id):
    conn = sqlite3.connect('hse_students.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM banned_users WHERE user_id = ?', (user_id,))
    count = cursor.fetchone()[0]
    conn.close()
    return count > 0

# Функция получения user_id по username
def get_user_id_by_username(username):
    # Убираем @ если есть
    if username.startswith('@'):
        username = username[1:]
    
    conn = sqlite3.connect('hse_students.db')
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM users WHERE username = ? OR username = ?', 
                   (username, '@' + username))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

# Клавиатуры
def get_campus_keyboard():
    keyboard = [
        [KeyboardButton("Москва")],
        [KeyboardButton("Санкт-Петербург")],
        [KeyboardButton("Нижний Новгород")],
        [KeyboardButton("Пермь")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

def get_education_level_keyboard():
    keyboard = [
        [KeyboardButton("Бакалавриат")],
        [KeyboardButton("Магистратура")],
        [KeyboardButton("Аспирантура")],
        [KeyboardButton("Специалитет")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

def get_course_keyboard():
    keyboard = [
        [KeyboardButton("1"), KeyboardButton("2")],
        [KeyboardButton("3"), KeyboardButton("4")],
        [KeyboardButton("5"), KeyboardButton("6")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

def get_profile_menu_keyboard():
    keyboard = [
        [KeyboardButton("👤 Посмотреть профиль")],
        [KeyboardButton("✏️ Редактировать профиль")],
        [KeyboardButton("🔙 Главное меню")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_edit_menu_keyboard():
    keyboard = [
        [KeyboardButton("📍 Изменить кампус"), KeyboardButton("👤 Изменить ФИ")],
        [KeyboardButton("🎓 Изменить ступень"), KeyboardButton("📚 Изменить курс")],
        [KeyboardButton("📋 Изменить программу"), KeyboardButton("🔙 Назад")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_building_keyboard():
    keyboard = [
        [KeyboardButton("Мясницкая")],
        [KeyboardButton("Покровка")],
        [KeyboardButton("Басманная")],
        [KeyboardButton("Трёхсвят")],
        [KeyboardButton("❌ Отменить")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

def get_experience_type_keyboard():
    keyboard = [
        [KeyboardButton("Присоединиться к кому-то")],
        [KeyboardButton("Создать рабочее место, видное другим")],
        [KeyboardButton("❌ Отменить")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

def get_close_workplace_keyboard():
    keyboard = [
        [KeyboardButton("Закрыть рабочее место")],
        [KeyboardButton("🔙 Главное меню")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_workplace_location_keyboard():
    keyboard = [
        [KeyboardButton("Библиотека 2 этаж (шумная)")],
        [KeyboardButton("Библиотека 3 этаж (тихая)")],
        [KeyboardButton("Библиотека 4 этаж (тихая)")],
        [KeyboardButton("Центральный атриум")],
        [KeyboardButton("Южный атриум")],
        [KeyboardButton("Аудитория")],
        [KeyboardButton("❌ Отменить создание")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

def get_search_location_keyboard():
    keyboard = [
        [KeyboardButton("Библиотека 2 этаж (шумная)")],
        [KeyboardButton("Библиотека 3 этаж (тихая)")],
        [KeyboardButton("Библиотека 4 этаж (тихая)")],
        [KeyboardButton("Центральный атриум")],
        [KeyboardButton("Южный атриум")],
        [KeyboardButton("Аудитории")],
        [KeyboardButton("❌ Отменить поиск")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

def get_main_menu_keyboard():
    keyboard = [
        [KeyboardButton("🔍 Найти компанию для учёбы")],
        [KeyboardButton("👤 Мой профиль")],
        [KeyboardButton("ℹ️ Помощь")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_admin_menu_keyboard():
    keyboard = [
        [KeyboardButton("🚫 Забанить пользователя")],
        [KeyboardButton("✅ Разбанить пользователя")],
        [KeyboardButton("📋 Список заблокированных")],
        [KeyboardButton("🔙 Главное меню")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# Функция проверки наличия профиля
def user_has_profile(user_id):
    conn = sqlite3.connect('hse_students.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM users WHERE user_id = ?', (user_id,))
    count = cursor.fetchone()[0]
    conn.close()
    return count > 0

# Функция проверки наличия рабочего места
def user_has_workplace(user_id):
    conn = sqlite3.connect('hse_students.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM workplaces WHERE user_id = ?', (user_id,))
    count = cursor.fetchone()[0]
    conn.close()
    return count > 0

# Декоратор для проверки бана
def check_ban(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if is_user_banned(user_id):
            await update.message.reply_text("❌ Вы заблокированы и не можете использовать бота.")
            return
        return await func(update, context)
    return wrapper

# Базовые обработчики

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    
    # Проверяем права администратора
    if is_admin(user):
        message = f"{WELCOME_TEXT}\n\n🔧 У вас есть права администратора!\n\nДавай создадим твой профиль - используй команду /create_profile\n\nДля получения помощи используй команду /help\n\nЗаблокировать - /ban @username причина\n\nРазблокировать - /unban @username\n\nСписок пользователей - /users\n\nСписок рабочих мест - /users_active\n\nЗавершить сессию пользователя - /end_session @username"
    else:
        message = f"{WELCOME_TEXT}\n\nДавай создадим твой профиль - используй команду /create_profile\n\nДля получения помощи используй команду /help"
    
    await update.message.reply_text(message, reply_markup=get_main_menu_keyboard())

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    await update.message.reply_text("По всем вопросам обращайтесь: @work_man02")

# Административные команды
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Админ-панель"""
    user = update.effective_user
    
    if not is_admin(user):
        await update.message.reply_text("❌ У вас нет прав администратора.")
        return
    
    await update.message.reply_text(
        "🔧 Админ-панель\n\nВыберите действие:",
        reply_markup=get_admin_menu_keyboard()
    )

async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Бан пользователя"""
    user = update.effective_user
    
    if not is_admin(user):
        await update.message.reply_text("❌ У вас нет прав администратора.")
        return
    
    # Если команда с аргументами
    if context.args:
        if len(context.args) < 2:
            await update.message.reply_text("❌ Использование: /ban @username причина")
            return
        
        target_username = context.args[0]
        reason = " ".join(context.args[1:])
        
        target_user_id = get_user_id_by_username(target_username)
        if not target_user_id:
            await update.message.reply_text(f"❌ Пользователь {target_username} не найден в базе данных.")
            return
        
        # Проверяем, не пытается ли админ забанить другого админа
        conn = sqlite3.connect('hse_students.db')
        cursor = conn.cursor()
        cursor.execute('SELECT username FROM users WHERE user_id = ?', (target_user_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0]:
            target_username_clean = result[0].replace('@', '')
            if target_username_clean.lower() in [admin.lower() for admin in ADMINS]:
                await update.message.reply_text("❌ Нельзя забанить администратора.")
                return
        
        # Баним пользователя
        conn = sqlite3.connect('hse_students.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO banned_users (user_id, banned_by, ban_reason)
            VALUES (?, ?, ?)
        ''', (target_user_id, f"@{user.username}", reason))
        conn.commit()
        conn.close()
        
        await update.message.reply_text(f"✅ Пользователь {target_username} заблокирован.\nПричина: {reason}")
    else:
        await update.message.reply_text("Введите username пользователя для бана (например: @username):")
        context.user_data['admin_action'] = 'ban_step1'

async def unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Разбан пользователя"""
    user = update.effective_user
    
    if not is_admin(user):
        await update.message.reply_text("❌ У вас нет прав администратора.")
        return
    
    if context.args:
        target_username = context.args[0]
        target_user_id = get_user_id_by_username(target_username)
        
        if not target_user_id:
            await update.message.reply_text(f"❌ Пользователь {target_username} не найден в базе данных.")
            return
        
        conn = sqlite3.connect('hse_students.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM banned_users WHERE user_id = ?', (target_user_id,))
        changes = cursor.rowcount
        conn.commit()
        conn.close()
        
        if changes > 0:
            await update.message.reply_text(f"✅ Пользователь {target_username} разблокирован.")
        else:
            await update.message.reply_text(f"❌ Пользователь {target_username} не был заблокирован.")
    else:
        await update.message.reply_text("Введите username пользователя для разбана (например: @username):")
        context.user_data['admin_action'] = 'unban_step1'

async def end_session(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Закрытие рабочего места пользователя администратором"""
    user = update.effective_user
    
    if not is_admin(user):
        await update.message.reply_text("❌ У вас нет прав администратора.")
        return
    
    if context.args:
        target_username = context.args[0]
        target_user_id = get_user_id_by_username(target_username)
        
        if not target_user_id:
            await update.message.reply_text(f"❌ Пользователь {target_username} не найден в базе данных.")
            return
        
        # Проверяем, есть ли у пользователя активное рабочее место
        conn = sqlite3.connect('hse_students.db')
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM workplaces WHERE user_id = ?', (target_user_id,))
        workplace_count = cursor.fetchone()[0]
        
        if workplace_count == 0:
            await update.message.reply_text(f"❌ У пользователя {target_username} нет активных рабочих мест.")
            conn.close()
            return
        
        # Получаем информацию о рабочем месте перед удалением
        cursor.execute('SELECT location, classroom FROM workplaces WHERE user_id = ?', (target_user_id,))
        workplace_info = cursor.fetchone()
        
        # Удаляем рабочее место
        cursor.execute('DELETE FROM workplaces WHERE user_id = ?', (target_user_id,))
        conn.commit()
        conn.close()
        
        workplace_location = workplace_info[0] if workplace_info else "неизвестная локация"
        classroom = f" ({workplace_info[1]})" if workplace_info and workplace_info[1] else ""
        
        await update.message.reply_text(
            f"✅ Рабочее место пользователя {target_username} в локации '{workplace_location}{classroom}' было закрыто администратором."
        )
        
        # Опционально: отправить уведомление пользователю (если бот может писать ему)
        try:
            await context.bot.send_message(
                chat_id=target_user_id,
                text=f"🔒 Ваше рабочее место в локации '{workplace_location}{classroom}' было закрыто администратором.\n\nВы можете создать новое рабочее место в любое время."
            )
        except Exception as e:
            # Если не удается отправить сообщение пользователю (например, он заблокировал бота)
            logger.warning(f"Не удалось отправить уведомление пользователю {target_user_id}: {e}")
    else:
        await update.message.reply_text("❌ Использование: /end_session @username")

async def join_workplace(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправка приглашения присоединиться к рабочему месту"""
    user = update.effective_user
    user_id = user.id
    
    # Проверяем бан
    if is_user_banned(user_id):
        await update.message.reply_text("❌ Вы заблокированы и не можете использовать бота.")
        return
    
    # Проверяем, есть ли профиль у пользователя
    if not user_has_profile(user_id):
        await update.message.reply_text("❌ Сначала создайте профиль командой /create_profile")
        return
    
    if context.args:
        target_username = context.args[0]
        target_user_id = get_user_id_by_username(target_username)
        
        if not target_user_id:
            await update.message.reply_text(f"❌ Пользователь {target_username} не найден в базе данных.")
            return
        
        if target_user_id == user_id:
            await update.message.reply_text("❌ Нельзя отправить приглашение самому себе.")
            return
        
        # Проверяем, есть ли у целевого пользователя активное рабочее место
        conn = sqlite3.connect('hse_students.db')
        cursor = conn.cursor()
        cursor.execute('SELECT location, classroom FROM workplaces WHERE user_id = ?', (target_user_id,))
        workplace_info = cursor.fetchone()
        
        if not workplace_info:
            await update.message.reply_text(f"❌ У пользователя {target_username} нет активного рабочего места.")
            conn.close()
            return
        
        # Получаем информацию о профиле отправителя
        cursor.execute('SELECT username, first_name, last_name, campus, education_level, course, program_name FROM users WHERE user_id = ?', (user_id,))
        sender_profile = cursor.fetchone()
        conn.close()
        
        if not sender_profile:
            await update.message.reply_text("❌ Ошибка получения вашего профиля.")
            return
        
        workplace_location = workplace_info[0]
        classroom = f" ({workplace_info[1]})" if workplace_info[1] else ""
        
        # Формируем карточку профиля отправителя
        sender_username, first_name, last_name, campus, education_level, course, program_name = sender_profile
        
        profile_card = f"""
📩 Приглашение присоединиться к рабочему месту!

👤 Кто хочет присоединиться:
- ФИ: {last_name} {first_name}
- Telegram: {sender_username or 'Не указан'}
- Кампус: {campus}
- Ступень: {education_level}
- Курс: {course}
- Программа: {program_name}

📍 Ваше рабочее место: {workplace_location}{classroom}

Если согласны принять этого студента, свяжитесь с ним напрямую!
        """
        
        # Отправляем уведомление владельцу рабочего места
        try:
            await context.bot.send_message(
                chat_id=target_user_id,
                text=profile_card
            )
            
            # Подтверждение отправителю
            await update.message.reply_text(
                f"✅ Приглашение отправлено пользователю {target_username}!\n"
                f"Ваша карточка профиля была отправлена владельцу рабочего места в локации '{workplace_location}{classroom}'."
            )
            
        except Exception as e:
            logger.warning(f"Не удалось отправить приглашение пользователю {target_user_id}: {e}")
            await update.message.reply_text(
                f"❌ Не удалось отправить приглашение пользователю {target_username}. "
                f"Возможно, он заблокировал бота или удалил чат."
            )
    else:
        await update.message.reply_text("❌ Использование: /join_workplace @username")

async def list_banned_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Список заблокированных пользователей"""
    user = update.effective_user
    
    if not is_admin(user):
        await update.message.reply_text("❌ У вас нет прав администратора.")
        return
    
    conn = sqlite3.connect('hse_students.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT u.username, u.first_name, u.last_name, b.banned_by, b.ban_reason, b.banned_at
        FROM banned_users b
        LEFT JOIN users u ON b.user_id = u.user_id
        ORDER BY b.banned_at DESC
    ''')
    banned_users = cursor.fetchall()
    conn.close()
    
    if not banned_users:
        await update.message.reply_text("📋 Список заблокированных пользователей пуст.")
        return
    
    message = "📋 Заблокированные пользователи:\n\n"
    for i, (username, first_name, last_name, banned_by, reason, banned_at) in enumerate(banned_users, 1):
        user_display = f"{first_name} {last_name}" if first_name and last_name else username or "Неизвестный"
        message += f"{i}. {user_display}\n"
        message += f"   👤 {username or 'Username не указан'}\n"
        message += f"   🚫 Заблокирован: {banned_by}\n"
        message += f"   📝 Причина: {reason}\n"
        message += f"   📅 Дата: {banned_at}\n\n"
    
    # Разбиваем длинное сообщение если нужно
    if len(message) > 4000:
        parts = message.split('\n\n')
        current_message = "📋 Заблокированные пользователи:\n\n"
        
        for part in parts[1:]:
            if len(current_message + part + '\n\n') > 4000:
                await update.message.reply_text(current_message)
                current_message = part + '\n\n'
            else:
                current_message += part + '\n\n'
        
        if current_message.strip():
            await update.message.reply_text(current_message)
    else:
        await update.message.reply_text(message)

async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Список всех зарегистрированных пользователей"""
    user = update.effective_user
    
    if not is_admin(user):
        await update.message.reply_text("❌ У вас нет прав администратора.")
        return
    
    conn = sqlite3.connect('hse_students.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT user_id, username, first_name, last_name, created_at
        FROM users
        ORDER BY created_at DESC
    ''')
    users = cursor.fetchall()
    conn.close()
    
    if not users:
        await update.message.reply_text("👥 В боте пока нет зарегистрированных пользователей.")
        return
    
    message = f"👥 Зарегистрированные пользователи ({len(users)} чел.):\n\n"
    for i, (user_id, username, first_name, last_name, created_at) in enumerate(users, 1):
        user_display = f"{last_name} {first_name}" if first_name and last_name else "Не указано"
        message += f"{i}. {user_id} - {user_display}\n"
        message += f"   📞 {username or 'Username не указан'}\n"
        message += f"   📅 Зарегистрирован: {created_at}\n\n"
    
    # Разбиваем длинное сообщение если нужно
    if len(message) > 4000:
        parts = message.split('\n\n')
        current_message = f"👥 Зарегистрированные пользователи ({len(users)} чел.):\n\n"
        
        for part in parts[1:]:
            if len(current_message + part + '\n\n') > 4000:
                await update.message.reply_text(current_message)
                current_message = part + '\n\n'
            else:
                current_message += part + '\n\n'
        
        if current_message.strip():
            await update.message.reply_text(current_message)
    else:
        await update.message.reply_text(message)

async def list_active_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Список пользователей с активными рабочими местами"""
    user = update.effective_user
    
    if not is_admin(user):
        await update.message.reply_text("❌ У вас нет прав администратора.")
        return
    
    conn = sqlite3.connect('hse_students.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT u.user_id, u.username, u.first_name, u.last_name, w.location, w.classroom, w.created_at
        FROM users u
        JOIN workplaces w ON u.user_id = w.user_id
        ORDER BY w.created_at DESC
    ''')
    active_users = cursor.fetchall()
    conn.close()
    
    if not active_users:
        await update.message.reply_text("🏢 Нет пользователей с активными рабочими местами.")
        return
    
    message = f"🏢 Пользователи с активными рабочими местами ({len(active_users)} чел.):\n\n"
    for i, (user_id, username, first_name, last_name, location, classroom, created_at) in enumerate(active_users, 1):
        user_display = f"{last_name} {first_name}" if first_name and last_name else "Не указано"
        workplace = f"{location}" + (f" ({classroom})" if classroom else "")
        message += f"{i}. {user_id} - {user_display} - {workplace}\n"
        message += f"   📞 {username or 'Username не указан'}\n"
        message += f"   🕐 Создано: {created_at}\n\n"
    
    # Разбиваем длинное сообщение если нужно
    if len(message) > 4000:
        parts = message.split('\n\n')
        current_message = f"🏢 Пользователи с активными рабочими местами ({len(active_users)} чел.):\n\n"
        
        for part in parts[1:]:
            if len(current_message + part + '\n\n') > 4000:
                await update.message.reply_text(current_message)
                current_message = part + '\n\n'
            else:
                current_message += part + '\n\n'
        
        if current_message.strip():
            await update.message.reply_text(current_message)
    else:
        await update.message.reply_text(message)

@check_ban
async def create_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало создания профиля"""
    user_id = update.effective_user.id
    
    # Проверяем, есть ли уже профиль у пользователя
    if user_has_profile(user_id):
        await update.message.reply_text(
            "У тебя уже есть профиль! Отредактируй его",
            reply_markup=get_profile_menu_keyboard()
        )
        return
    
    await update.message.reply_text(
        "Давайте создадим ваш профиль!\n\n📍 Выберите кампус (список будет пополняться):",
        reply_markup=get_campus_keyboard()
    )
    context.user_data['step'] = 'campus'

@check_ban
async def handle_profile_creation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка создания профиля по шагам"""
    user_data = context.user_data
    user_id = update.effective_user.id
    
    if user_data.get('step') == 'campus':
        user_data['campus'] = update.message.text
        await update.message.reply_text(
            "👤 Введите ваши Фамилию и Имя (например: Иванов Иван):"
        )
        user_data['step'] = 'fullname'
        
    elif user_data.get('step') == 'fullname':
        fullname = update.message.text.strip()
        if ' ' in fullname:
            parts = fullname.split(' ', 1)
            user_data['last_name'] = parts[0]
            user_data['first_name'] = parts[1]
            await update.message.reply_text(
                "🎓 Выберите ступень образования:",
                reply_markup=get_education_level_keyboard()
            )
            user_data['step'] = 'education_level'
        else:
            await update.message.reply_text("Пожалуйста, введите Фамилию и Имя через пробел.")
            
    elif user_data.get('step') == 'education_level':
        user_data['education_level'] = update.message.text
        await update.message.reply_text(
            "📚 Выберите курс:",
            reply_markup=get_course_keyboard()
        )
        user_data['step'] = 'course'
        
    elif user_data.get('step') == 'course':
        try:
            course = int(update.message.text)
            if 1 <= course <= 6:
                user_data['course'] = course
                await update.message.reply_text(
                    "📋 Введите название образовательной программы:\n\n"
                    "Например: Экономика, Прикладная математика и информатика, Юриспруденция"
                )
                user_data['step'] = 'program_name'
            else:
                await update.message.reply_text("Пожалуйста, выберите курс от 1 до 6.")
        except ValueError:
            await update.message.reply_text("Пожалуйста, введите номер курса (1-6).")
            
    elif user_data.get('step') == 'program_name':
        user_data['program_name'] = update.message.text.strip()
        await update.message.reply_text(
            "🔢 Введите код образовательной программы:\n\n"
            "Код можно найти на сайте ВШЭ: https://clck.ru/3PKQuC\n"
            "Например: 38.03.01"
        )
        user_data['step'] = 'program_code'
            
    elif user_data.get('step') == 'program_code':
        user_data['program_code'] = update.message.text.strip()
        
        # Сохранение в базу данных
        conn = sqlite3.connect('hse_students.db')
        cursor = conn.cursor()
        
        # Получаем username с @ или без него
        username = update.effective_user.username
        if username and not username.startswith('@'):
            username = '@' + username
        
        cursor.execute('''
            INSERT OR REPLACE INTO users 
            (user_id, username, first_name, last_name, campus, education_level, course, program_name, program_code)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id,
            username,
            user_data['first_name'],
            user_data['last_name'],
            user_data['campus'],
            user_data['education_level'],
            user_data['course'],
            user_data['program_name'],
            user_data['program_code']
        ))
        
        conn.commit()
        conn.close()
        
        # Подтверждение создания профиля
        profile_info = f"""
✅ Профиль успешно создан и сохранен!

👤 ФИ: {user_data['last_name']} {user_data['first_name']}
📞 Telegram: {username if username else 'Не указан'}
📍 Кампус: {user_data['campus']}
🎓 Ступень: {user_data['education_level']}
📚 Курс: {user_data['course']}
📋 Программа: {user_data['program_name']}
🔢 Код программы: {user_data['program_code']}

Ваш профиль теперь привязан к вашему Telegram ID и будет сохранен!
        """
        
        await update.message.reply_text(profile_info)
        
        # Предложение действий с профилем
        await update.message.reply_text(
            "Что хотите сделать дальше?",
            reply_markup=get_main_menu_keyboard()
        )
        
        # Очистка данных сессии
        context.user_data.clear()

@check_ban
async def view_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Просмотр профиля пользователя"""
    user_id = update.effective_user.id
    
    conn = sqlite3.connect('hse_students.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    profile = cursor.fetchone()
    conn.close()
    
    if profile:
        message = f"""
👤 Ваш профиль:

ФИ: {profile[3]} {profile[2]}
📞 Telegram: {profile[1] if profile[1] else 'Не указан'}
📍 Кампус: {profile[4]}
🎓 Ступень: {profile[5]}
📚 Курс: {profile[6]}
📋 Программа: {profile[7]}
🔢 Код программы: {profile[8]}
        """
        await update.message.reply_text(message, reply_markup=get_profile_menu_keyboard())
    else:
        await update.message.reply_text("У вас нет профиля. Создайте его командой /create_profile")

@check_ban
async def edit_profile_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Меню редактирования профиля"""
    await update.message.reply_text(
        "Что хотите изменить в профиле?",
        reply_markup=get_edit_menu_keyboard()
    )

@check_ban
async def find_study_buddy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало поиска компании для учёбы"""
    await update.message.reply_text(
        "🏢 Выберите корпус для поиска компании:",
        reply_markup=get_building_keyboard()
    )
    context.user_data['search_step'] = 'building'

@check_ban
async def close_workplace(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Закрытие рабочего места"""
    user_id = update.effective_user.id
    
    conn = sqlite3.connect('hse_students.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM workplaces WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()
    
    await update.message.reply_text(
        "✅ Рабочее место закрыто!",
        reply_markup=get_main_menu_keyboard()
    )

async def show_workplace_users(update: Update, context: ContextTypes.DEFAULT_TYPE, location: str):
    """Показать пользователей с рабочими местами в определенной локации"""
    conn = sqlite3.connect('hse_students.db')
    cursor = conn.cursor()
    
    if location == "Аудитории":
        # Показать всех пользователей в аудиториях
        cursor.execute('''
            SELECT u.first_name, u.last_name, u.username, u.education_level, u.course, u.program_name, w.classroom
            FROM users u 
            JOIN workplaces w ON u.user_id = w.user_id 
            WHERE w.location = "Аудитория"
        ''')
    else:
        # Показать пользователей в конкретной локации
        cursor.execute('''
            SELECT u.first_name, u.last_name, u.username, u.education_level, u.course, u.program_name
            FROM users u 
            JOIN workplaces w ON u.user_id = w.user_id 
            WHERE w.location = ?
        ''', (location,))
    
    users = cursor.fetchall()
    conn.close()
    
    if not users:
        await update.message.reply_text(
            f"В локации '{location}' пока никто не создал рабочее место.",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    message = f"Чтобы присоединиться, напиши команду /join_workplace @username\n\n👥 Студенты в локации '{location}':\n\n"
    
    for i, user in enumerate(users, 1):
        if location == "Аудитории":
            # Для аудиторий показываем номер аудитории
            message += f"{i}. {user[1]} {user[0]}\n"
            message += f"📞 {user[2] if user[2] else 'Не указан'}\n"
            message += f"🎓 {user[3]}, {user[4]} курс\n"
            message += f"📋 {user[5]}\n"
            message += f"🚪 Аудитория: {user[6]}\n\n"
        else:
            message += f"{i}. {user[1]} {user[0]}\n"
            message += f"📞 {user[2] if user[2] else 'Не указан'}\n"
            message += f"🎓 {user[3]}, {user[4]} курс\n"
            message += f"📋 {user[5]}\n\n"
    
    # Telegram имеет ограничение на длину сообщения
    if len(message) > 4000:
        # Разбиваем сообщение на части
        parts = message.split('\n\n')
        current_message = f"Чтобы присоединиться, напиши команду /join_workplace @username\n\n👥 Студенты в локации '{location}':\n\n"
        
        for part in parts[1:]:  # Пропускаем заголовок
            if len(current_message + part + '\n\n') > 4000:
                await update.message.reply_text(current_message)
                current_message = part + '\n\n'
            else:
                current_message += part + '\n\n'
        
        if current_message.strip():
            await update.message.reply_text(current_message, reply_markup=get_main_menu_keyboard())
    else:
        await update.message.reply_text(message, reply_markup=get_main_menu_keyboard())

async def save_workplace(update: Update, context: ContextTypes.DEFAULT_TYPE, location: str, classroom: str = None):
    """Сохранение рабочего места в базу данных"""
    user_id = update.effective_user.id
    
    conn = sqlite3.connect('hse_students.db')
    cursor = conn.cursor()
    
    # Удаляем старые рабочие места пользователя
    cursor.execute('DELETE FROM workplaces WHERE user_id = ?', (user_id,))
    
    # Добавляем новое рабочее место
    cursor.execute('''
        INSERT INTO workplaces (user_id, location, classroom)
        VALUES (?, ?, ?)
    ''', (user_id, location, classroom))
    
    conn.commit()
    conn.close()
    
    # Отправляем подтверждение с кнопкой закрытия
    await update.message.reply_text(
        "Отлично! Теперь другие студенты могут к тебе присоединиться. Жди сообщения от них в телеграмм и не забудь разрешить уведомления для незнакомых контактов!\n\n💡 Закрой рабочее место, если уже нашел себе компанию",
        reply_markup=get_close_workplace_keyboard()
    )
    
    # Очистка временных данных поиска
    context.user_data.pop('search_step', None)
    context.user_data.pop('temp_building', None)
    context.user_data.pop('temp_experience_type', None)
    context.user_data.pop('temp_location', None)

async def cancel_workplace_creation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена создания рабочего места"""
    # Очистка всех временных данных поиска и создания рабочего места
    context.user_data.pop('search_step', None)
    context.user_data.pop('temp_building', None)
    context.user_data.pop('temp_experience_type', None)
    context.user_data.pop('temp_location', None)
    
    await update.message.reply_text(
        "❌ Создание рабочего места отменено.",
        reply_markup=get_main_menu_keyboard()
    )

async def cancel_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена поиска компании"""
    # Очистка всех временных данных поиска
    context.user_data.pop('search_step', None)
    context.user_data.pop('temp_building', None)
    context.user_data.pop('temp_experience_type', None)
    context.user_data.pop('temp_location', None)
    
    await update.message.reply_text(
        "❌ Поиск компании отменен.",
        reply_markup=get_main_menu_keyboard()
    )

@check_ban
async def handle_study_buddy_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка поиска компании для учёбы"""
    search_step = context.user_data.get('search_step')
    text = update.message.text
    
    # Проверка на отмену на любом этапе
    if text in ["❌ Отменить", "❌ Отменить создание", "❌ Отменить поиск"]:
        if text == "❌ Отменить поиск":
            await cancel_search(update, context)
        else:
            await cancel_workplace_creation(update, context)
        return
    
    if search_step == 'building':
        building = text
        if building != "Покровка":
            await update.message.reply_text(
                "К сожалению, на данный момент бот работает только для покровки. Попробуй поискать компанию там!",
                reply_markup=get_building_keyboard()
            )
            return
        
        context.user_data['temp_building'] = building
        await update.message.reply_text(
            "Ты хочешь...",
            reply_markup=get_experience_type_keyboard()
        )
        context.user_data['search_step'] = 'experience_type'
        
    elif search_step == 'experience_type':
        experience_type = text
        context.user_data['temp_experience_type'] = experience_type
        
        if experience_type == "Присоединиться к кому-то":
            await update.message.reply_text(
                "🔍 Выберите место для поиска:",
                reply_markup=get_search_location_keyboard()
            )
            context.user_data['search_step'] = 'search_location'
        else:  # "Создать рабочее место, видное другим"
            user_id = update.effective_user.id
            if user_has_workplace(user_id):
                await update.message.reply_text(
                    "У вас уже есть активное рабочее место!",
                    reply_markup=get_close_workplace_keyboard()
                )
                # Очистка временных данных поиска
                context.user_data.pop('search_step', None)
                context.user_data.pop('temp_building', None)
                context.user_data.pop('temp_experience_type', None)
            else:
                await update.message.reply_text(
                    "📍 Выберите место для учёбы:",
                    reply_markup=get_workplace_location_keyboard()
                )
                context.user_data['search_step'] = 'workplace_location'
    
    elif search_step == 'search_location':
        location = text
        await show_workplace_users(update, context, location)
        
        # Очистка временных данных поиска
        context.user_data.pop('search_step', None)
        context.user_data.pop('temp_building', None)
        context.user_data.pop('temp_experience_type', None)
    
    elif search_step == 'workplace_location':
        location = text
        context.user_data['temp_location'] = location
        
        if location == "Аудитория":
            await update.message.reply_text(
                "напиши номер аудитории вместе с буквой, например, G603\n\n❌ Для отмены напишите 'отмена'"
            )
            context.user_data['search_step'] = 'classroom_number'
        else:
            # Сохранение рабочего места в БД
            await save_workplace(update, context, location, None)
    
    elif search_step == 'classroom_number':
        classroom = text.strip()
        
        # Проверка на отмену
        if classroom.lower() in ['отмена', 'отменить', '❌ отмена', '❌']:
            await cancel_workplace_creation(update, context)
            return
            
        location = context.user_data.get('temp_location', 'Аудитория')
        
        # Сохранение рабочего места в БД
        await save_workplace(update, context, location, classroom)

async def handle_menu_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка действий из меню"""
    text = update.message.text
    
    # Проверка на отмену на любом этапе
    if text in ["❌ Отменить", "❌ Отменить создание", "❌ Отменить поиск"]:
        if text == "❌ Отменить поиск":
            await cancel_search(update, context)
        else:
            await cancel_workplace_creation(update, context)
        return
    
    if text == "🔍 Найти компанию для учёбы":
        await find_study_buddy(update, context)
    elif text == "👤 Мой профиль":
        await view_profile(update, context)
    elif text == "ℹ️ Помощь":
        await help_command(update, context)
    elif text == "👤 Посмотреть профиль":
        await view_profile(update, context)
    elif text == "✏️ Редактировать профиль":
        await edit_profile_menu(update, context)
    elif text == "🔙 Главное меню" or text == "🔙 Назад":
        await update.message.reply_text(
            "Главное меню:",
            reply_markup=get_main_menu_keyboard()
        )
    elif text == "Закрыть рабочее место":
        await close_workplace(update, context)
    elif text == "📍 Изменить кампус":
        await update.message.reply_text(
            "Выберите новый кампус:",
            reply_markup=get_campus_keyboard()
        )
        context.user_data['edit_step'] = 'campus'
    elif text == "👤 Изменить ФИ":
        await update.message.reply_text("Введите новые Фамилию и Имя (через пробел):")
        context.user_data['edit_step'] = 'fullname'
    elif text == "🎓 Изменить ступень":
        await update.message.reply_text(
            "Выберите новую ступень образования:",
            reply_markup=get_education_level_keyboard()
        )
        context.user_data['edit_step'] = 'education_level'
    elif text == "📚 Изменить курс":
        await update.message.reply_text(
            "Выберите новый курс:",
            reply_markup=get_course_keyboard()
        )
        context.user_data['edit_step'] = 'course'
    elif text == "📋 Изменить программу":
        await update.message.reply_text("Введите новое название программы:")
        context.user_data['edit_step'] = 'program_name'
    # Админские действия
    elif text == "🚫 Забанить пользователя":
        await update.message.reply_text("Введите username пользователя для бана (например: @username):")
        context.user_data['admin_action'] = 'ban_step1'
    elif text == "✅ Разбанить пользователя":
        await update.message.reply_text("Введите username пользователя для разбана (например: @username):")
        context.user_data['admin_action'] = 'unban_step1'
    elif text == "📋 Список заблокированных":
        await list_banned_users(update, context)

async def handle_profile_editing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка редактирования профиля"""
    edit_step = context.user_data.get('edit_step')
    user_id = update.effective_user.id
    
    if edit_step == 'campus':
        new_value = update.message.text
        field = 'campus'
    elif edit_step == 'fullname':
        fullname = update.message.text.strip()
        if ' ' in fullname:
            parts = fullname.split(' ', 1)
            # Обновляем два поля одновременно
            conn = sqlite3.connect('hse_students.db')
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE users SET last_name = ?, first_name = ? WHERE user_id = ?',
                (parts[0], parts[1], user_id)
            )
            conn.commit()
            conn.close()
            await update.message.reply_text(
                f"✅ ФИ обновлено на: {parts[0]} {parts[1]}",
                reply_markup=get_profile_menu_keyboard()
            )
            context.user_data.clear()
            return
        else:
            await update.message.reply_text("Пожалуйста, введите Фамилию и Имя через пробел.")
            return
    elif edit_step == 'education_level':
        new_value = update.message.text
        field = 'education_level'
    elif edit_step == 'course':
        try:
            new_value = int(update.message.text)
            if not (1 <= new_value <= 6):
                await update.message.reply_text("Пожалуйста, выберите курс от 1 до 6.")
                return
            field = 'course'
        except ValueError:
            await update.message.reply_text("Пожалуйста, введите номер курса (1-6).")
            return
    elif edit_step == 'program_name':
        context.user_data['new_program_name'] = update.message.text.strip()
        await update.message.reply_text("Теперь введите код программы:")
        context.user_data['edit_step'] = 'program_code'
        return
    elif edit_step == 'program_code':
        # Обновляем название и код программы
        conn = sqlite3.connect('hse_students.db')
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE users SET program_name = ?, program_code = ? WHERE user_id = ?',
            (context.user_data['new_program_name'], update.message.text.strip(), user_id)
        )
        conn.commit()
        conn.close()
        await update.message.reply_text(
            f"✅ Программа обновлена на: {context.user_data['new_program_name']} ({update.message.text.strip()})",
            reply_markup=get_profile_menu_keyboard()
        )
        context.user_data.clear()
        return
    else:
        return
    
    # Обновление одного поля
    conn = sqlite3.connect('hse_students.db')
    cursor = conn.cursor()
    cursor.execute(f'UPDATE users SET {field} = ? WHERE user_id = ?', (new_value, user_id))
    conn.commit()
    conn.close()
    
    await update.message.reply_text(
        f"✅ {field.replace('_', ' ').title()} обновлено на: {new_value}",
        reply_markup=get_profile_menu_keyboard()
    )
    context.user_data.clear()

async def handle_admin_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка админских действий"""
    admin_action = context.user_data.get('admin_action')
    user = update.effective_user
    
    if not is_admin(user):
        await update.message.reply_text("❌ У вас нет прав администратора.")
        return
    
    if admin_action == 'ban_step1':
        target_username = update.message.text.strip()
        context.user_data['ban_target'] = target_username
        await update.message.reply_text("Введите причину бана:")
        context.user_data['admin_action'] = 'ban_step2'
        
    elif admin_action == 'ban_step2':
        reason = update.message.text.strip()
        target_username = context.user_data.get('ban_target')
        
        target_user_id = get_user_id_by_username(target_username)
        if not target_user_id:
            await update.message.reply_text(f"❌ Пользователь {target_username} не найден в базе данных.")
            context.user_data.clear()
            return
        
        # Проверяем, не пытается ли админ забанить другого админа
        conn = sqlite3.connect('hse_students.db')
        cursor = conn.cursor()
        cursor.execute('SELECT username FROM users WHERE user_id = ?', (target_user_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0]:
            target_username_clean = result[0].replace('@', '')
            if target_username_clean.lower() in [admin.lower() for admin in ADMINS]:
                await update.message.reply_text("❌ Нельзя забанить администратора.")
                context.user_data.clear()
                return
        
        # Баним пользователя
        conn = sqlite3.connect('hse_students.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO banned_users (user_id, banned_by, ban_reason)
            VALUES (?, ?, ?)
        ''', (target_user_id, f"@{user.username}", reason))
        conn.commit()
        conn.close()
        
        await update.message.reply_text(
            f"✅ Пользователь {target_username} заблокирован.\nПричина: {reason}",
            reply_markup=get_admin_menu_keyboard()
        )
        context.user_data.clear()
        
    elif admin_action == 'unban_step1':
        target_username = update.message.text.strip()
        target_user_id = get_user_id_by_username(target_username)
        
        if not target_user_id:
            await update.message.reply_text(f"❌ Пользователь {target_username} не найден в базе данных.")
            context.user_data.clear()
            return
        
        conn = sqlite3.connect('hse_students.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM banned_users WHERE user_id = ?', (target_user_id,))
        changes = cursor.rowcount
        conn.commit()
        conn.close()
        
        if changes > 0:
            await update.message.reply_text(
                f"✅ Пользователь {target_username} разблокирован.",
                reply_markup=get_admin_menu_keyboard()
            )
        else:
            await update.message.reply_text(
                f"❌ Пользователь {target_username} не был заблокирован.",
                reply_markup=get_admin_menu_keyboard()
            )
        context.user_data.clear()

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений"""
    if context.user_data.get('step'):
        await handle_profile_creation(update, context)
    elif context.user_data.get('edit_step'):
        await handle_profile_editing(update, context)
    elif context.user_data.get('search_step'):
        await handle_study_buddy_search(update, context)
    elif context.user_data.get('admin_action'):
        await handle_admin_actions(update, context)
    elif update.message.text in ["🔍 Найти компанию для учёбы", "👤 Мой профиль", "ℹ️ Помощь",
                                  "👤 Посмотреть профиль", "✏️ Редактировать профиль", "🔙 Главное меню", "🔙 Назад", 
                                  "📍 Изменить кампус", "👤 Изменить ФИ", "🎓 Изменить ступень", "📚 Изменить курс", "📋 Изменить программу",
                                  "Мясницкая", "Покровка", "Басманная", "Трёхсвят",
                                  "Присоединиться к кому-то", "Создать рабочее место, видное другим",
                                  "Библиотека 2 этаж (шумная)", "Библиотека 3 этаж (тихая)", "Библиотека 4 этаж (тихая)",
                                  "Центральный атриум", "Южный атриум", "Аудитория", "Аудитории",
                                  "Закрыть рабочее место", "🚫 Забанить пользователя", "✅ Разбанить пользователя", "📋 Список заблокированных",
                                  "❌ Отменить", "❌ Отменить создание", "❌ Отменить поиск"]:
        await handle_menu_actions(update, context)
    else:
        # Проверяем бан перед ответом
        user_id = update.effective_user.id
        if is_user_banned(user_id):
            await update.message.reply_text("❌ Вы заблокированы и не можете использовать бота.")
            return
        await update.message.reply_text(f"Вы написали: {update.message.text}")

def main():
    """Главная функция - запуск бота"""
    # Инициализация базы данных
    init_db()
    
    # Создание приложения
    application = Application.builder().token(BOT_TOKEN).build()

    # Добавление обработчиков
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("create_profile", create_profile))
    application.add_handler(CommandHandler("admin", admin_panel))
    application.add_handler(CommandHandler("ban", ban_user))
    application.add_handler(CommandHandler("unban", unban_user))
    application.add_handler(CommandHandler("banned", list_banned_users))
    application.add_handler(CommandHandler("users", list_users))
    application.add_handler(CommandHandler("users_active", list_active_users))
    application.add_handler(CommandHandler("end_session", end_session))
    application.add_handler(CommandHandler("join_workplace", join_workplace))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # Запуск бота
    print("Бот запущен...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
