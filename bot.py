from telegram import Update
from telegram.ext import filters, Application, CommandHandler, MessageHandler, ContextTypes, ChatJoinRequestHandler

# Хранилище правильных ответов
correct_users = []

# Хранилище отклонённых пользователей
declined_users = []

# ID администратора
ADMIN_ID = 806048645

# Вопрос и правильный ответ
QUESTION = "Вы бизнесмен?"
CORRECT_ANSWER = "царевич"

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
    if is_suspicious:
        declined_users.append({
            'user_id': user.id,
            'username': user.username,
            'full_name': user.full_name,
            'reason': reason
        })
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

    chat_id = user_data.get('chat_id')
    if not chat_id:
        await update.message.reply_text("Произошла ошибка: отсутствует chat_id.")
        return

    if answer == CORRECT_ANSWER:
        correct_users.append({
            'user_id': user.id,
            'full_name': user.full_name
        })
        await context.bot.approve_chat_join_request(chat_id, user.id)
        await update.message.reply_text("Ваш ответ правильный! Вы добавлены в группу.")
    else:
        declined_users.append({
            'user_id': user.id,
            'username': user.username,
            'full_name': user.full_name,
            'reason': "Неправильный ответ"
        })
        await context.bot.decline_chat_join_request(chat_id, user.id)
        await update.message.reply_text("Ответ неправильный. Вы не можете быть добавлены в группу.")

async def list_correct(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Просмотр принятых пользователей"""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("У вас нет прав для выполнения этой команды.")
        return

    if not correct_users:
        await update.message.reply_text("Нет принятых пользователей.")
        return

    response = "Список принятых пользователей:\n\n"
    for user in correct_users:
        response += f"ID: {user['user_id']}, Имя: {user['full_name']}\n"

    await update.message.reply_text(response)

async def list_declined_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Просмотр отклонённых пользователей"""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("У вас нет прав для выполнения этой команды.")
        return

    if not declined_users:
        await update.message.reply_text("Нет отклонённых пользователей.")
        return

    response = "Список отклонённых пользователей:\n\n"
    for user in declined_users:
        response += f"ID: {user['user_id']}, Ник: {user['username']}, Имя: {user['full_name']}, Причина: {user['reason']}\n"

    await update.message.reply_text(response)

if __name__ == "__main__":
    TOKEN = "8046428888:AAE6subVaWXogC7rm3VxmxTYFG9PNKRxuHI"
    app = Application.builder().token(TOKEN).build()

    # Обработчик для заявок на вступление
    app.add_handler(ChatJoinRequestHandler(handle_join_request))
    # Обработчик ответов пользователей
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_answer))
    # Команда для просмотра отклонённых пользователей
    app.add_handler(CommandHandler("decline_list", list_declined_users))
    # Добавляем обработчик для команды list_correct
    app.add_handler(CommandHandler("list_correct", list_correct))

    print("Бот запущен...")
    app.run_polling()
