from aiogram import Bot, Dispatcher, types
from aiogram.types import ChatJoinRequest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
import asyncio
# Вставьте токен вашего бота от BotFather
API_TOKEN = "8046428888:AAE6subVaWXogC7rm3VxmxTYFG9PNKRxuHI"

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


# Состояния для FSM (Finite State Machine)
class JoinRequest(StatesGroup):
    waiting_for_answer = State()


# Обработка запроса на вступление
@dp.chat_join_request()
async def handle_join_request(request: types.ChatJoinRequest):
    # Получаем данные о пользователе
    user = request.from_user
    chat_id = request.chat.id

    # Сохраняем ID группы и пользователя для последующей обработки
    await bot.send_message(
        chat_id=user.id,
        text=(
            f"Привет, {user.full_name}! Перед вступлением в группу, ответьте на следующий вопрос:\n"
            "Какая цель вашего вступления в эту группу?"
        ),
    )

    # Устанавливаем состояние пользователя через FSMContext
    await state.set_state(JoinRequest.waiting_for_answer)

    # Сохраняем данные для проверки
    await dp.storage.set_data(chat=user.id, data={"chat_id": chat_id, "user_id": user.id})


# Обработка ответа пользователя
@dp.message(JoinRequest.waiting_for_answer)
async def collect_answer(message: types.Message, state: FSMContext):
    # Получаем сохраненные данные
    data = await state.get_data()
    chat_id = data.get("chat_id")
    user_id = data.get("user_id")

    # Проверяем ответ
    if "инвестировать" in message.text.lower():
        # Одобряем запрос
        await bot.approve_chat_join_request(chat_id=chat_id, user_id=user_id)
        await message.answer("Спасибо за ваш ответ! Добро пожаловать в группу.")
    else:
        # Отклоняем запрос
        await bot.decline_chat_join_request(chat_id=chat_id, user_id=user_id)
        await message.answer("Ваш ответ не соответствует требованиям группы.")

    # Завершаем состояние
    await state.clear()


async def main():
    # Запуск polling
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
