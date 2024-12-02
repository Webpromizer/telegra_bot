from telegram import Update
from telegram.ext import filters, Application, CommandHandler, MessageHandler, ContextTypes, ChatJoinRequestHandler

# Хранилище пользователей с их ответами
users_data = []

# ID администратора
ADMIN_ID = 806048645

# Вопрос и правильный ответ
QUESTION = "Вы бизнесмен?"

# Включаем логирование
import logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

async def is_suspicious_user(user, update):
    """Проверяет пользователя на подозрительное поведение."""
    # Проверка: является ли ботом
    if user.is_bot:
        return True, "Пользователь является ботом."

    # Если пользователь не подозрителен
    return False, None


async def handle_join_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка запроса на вступление в канал"""
    chat_join_request = update.chat_join_request
    user = chat_join_request.from_user

    # Проверка пользователя на подозрительность
    is_suspicious, reason = await is_suspicious_user(user, update)
    
    # Сохраняем информацию о пользователе
    users_data.append({
        'user_id': user.id,
        'full_name': user.full_name,
        'username': user.username,
        'suspicious': is_suspicious,
        'answer': None,
        'chat_id': chat_join_request.chat.id  # Сохраняем chat_id для добавления позже
    })

    if is_suspicious:
        await context.bot.decline_chat_join_request(chat_join_request.chat.id, user.id)
        return

    # Отправляем вопрос пользователю
    await context.bot.send_message(
        chat_id=user.id,
        text=f"Здравствуйте, {user.full_name}! {QUESTION}"
    )
    context.user_data[user.id] = {
        'awaiting_answer': True,
        'chat_id': chat_join_request.chat.id
    }

async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ответа пользователя"""
    user = update.effective_user
    user_data = context.user_data.setdefault(user.id, {})

    if not user_data.get('awaiting_answer'):
        await update.message.reply_text("Вы не подавали заявку или уже ответили.")
        return

    context.user_data[user.id]['awaiting_answer'] = False
    answer = update.message.text.strip().lower()

    # Обновляем ответ пользователя
    for data in users_data:
        if data['user_id'] == user.id:
            data['answer'] = answer

    await context.bot.send_message(
        chat_id=user.id,
        text="Ваш ответ сохранен. Пожалуйста, ожидайте проверки администратором."
    )

async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Просмотр всех пользователей с их ответами и подозрительностью"""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("У вас нет прав для выполнения этой команды.")
        return

    if not users_data:
        await update.message.reply_text("Нет пользователей.")
        return

    response = "Список пользователей:\n\n"
    for idx, user in enumerate(users_data, 1):
        suspicious = "Да" if user['suspicious'] else "Нет"
        answer = user['answer'] if user['answer'] else "Не ответил"
        response += f"{idx}. Имя: {user['full_name']}, Подозрительность: {suspicious}, Ответ: {answer}\n"

    await update.message.reply_text(response)

async def add_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Добавление всех пользователей, которые ответили на вопрос"""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("У вас нет прав для выполнения этой команды.")
        return

    added_users = []
    for user in users_data:
        if user['answer']:  # Проверяем, что пользователь ответил на вопрос
            added_users.append(user)

    if not added_users:
        await update.message.reply_text("Нет пользователей с ответом на вопрос.")
        return

    for user in added_users:
        chat_id = user['chat_id']
        await context.bot.approve_chat_join_request(update.message.chat.id, chat_id)

    await update.message.reply_text(f"Добавлены следующие пользователи:\n" + "\n".join([user['full_name'] for user in added_users]))

async def handle_chat_join_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка события одобрения или отклонения заявки пользователем"""
    if update.chat_join_request.approved:
        action = "одобрен"
    else:
        action = "отклонен"

    user_id = update.chat_join_request.from_user.id
    # Удаляем данные о пользователе после одобрения или отклонения заявки
    users_data[:] = [user for user in users_data if user['user_id'] != user_id]

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"Заявка пользователя {user_id} {action}."
    )

if __name__ == "__main__":
    TOKEN = "8046428888:AAE6subVaWXogC7rm3VxmxTYFG9PNKRxuHI"
    app = Application.builder().token(TOKEN).build()

    # Обработчик для заявок на вступление
    app.add_handler(ChatJoinRequestHandler(handle_join_request))
    # Обработчик ответов пользователей
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_answer))
    # Команда для просмотра списка пользователей
    app.add_handler(CommandHandler("show_users", list_users))
    # Команда для добавления всех пользователей, которые ответили
    app.add_handler(CommandHandler("add_users", add_users))
    # Обработчик для событий одобрения или отклонения заявки
    app.add_handler(ChatJoinRequestHandler(handle_chat_join_update))

    print("Бот запущен...")
    app.run_polling()
