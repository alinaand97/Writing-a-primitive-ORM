# Витамины для всех!
import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils import executor

from crud_functions import initiate_db, get_all_products, add_user, is_included   # Импортируем функции


api=''
bot = Bot(token = api)
storage = MemoryStorage()
dp = Dispatcher(bot, storage = MemoryStorage())

# Инициализация базы данных
initiate_db()

# Определение состояний
class UserState(StatesGroup):
    age = State()
    growth = State()
    weight = State()

class RegistrationState(StatesGroup):
    username = State()
    email = State()
    age = State()

# Создание клавиатуры
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# Обычная клавиатура
keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
button_calculate = KeyboardButton('Рассчитать')
button_info = KeyboardButton('Информация')
button_buy = KeyboardButton('Купить')
button_register = KeyboardButton('Регистрация')
keyboard.add(button_calculate, button_info, button_buy, button_register)

# Inline клавиатура
inline_keyboard = InlineKeyboardMarkup()
button_calories = InlineKeyboardButton('Рассчитать норму калорий', callback_data='calories')
button_formulas = InlineKeyboardButton('Формулы расчёта', callback_data='formulas')
inline_keyboard.add(button_calories, button_formulas)

#Inline меню для покупки продуктов
product_inline_keyboard = InlineKeyboardMarkup()
for i in range(1, 5):
    product_button = InlineKeyboardButton(f'Product{i}', callback_data='product_buying')
    product_inline_keyboard.add(product_button)

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer("Выберите действие:", reply_markup=keyboard)

@dp.message_handler(lambda message: message.text == 'Рассчитать')
async def main_menu(message: types.Message):
    await message.answer('Выберите опцию:', reply_markup=inline_keyboard)

@dp.message_handler(lambda message: message.text == 'Купить')  # Обработчик для кнопки "Купить"
async def get_buying_list(message: types.Message):
    products = get_all_products()  # Получаем все продукты из базы данных
    for title, description, price in products:
        product_info = f'Название: {title} | Описание: {description} | Цена: {price}'
        photo_path = f'{title}.jpg'
        with open(photo_path, 'rb') as photo:
            await message.answer(product_info)
            await bot.send_photo(message.chat.id, photo)
    await message.answer("Выберите продукт для покупки:", reply_markup=product_inline_keyboard)

@dp.message_handler(lambda message: message.text == 'Информация')
async def main_menu(message: types.Message):
    await message.answer('Информация о боте')

@dp.callback_query_handler(lambda call: call.data == 'formulas')
async def get_formulas(call: types.CallbackQuery):
    await call.message.answer('Формула Миффлина-Сан Жеора: 10  вес + 6.25  рост - 5  возраст + 5')

@dp.callback_query_handler(lambda call: call.data == 'calories')
async def set_age(call: types.CallbackQuery):
    await call.message.answer('Введите свой возраст:')
    await UserState.age.set()

@dp.message_handler(state=UserState.age)
async def set_growth(message: types.Message, state: FSMContext):
    await state.update_data(age=message.text)
    await message.answer('Введите свой рост:')
    await UserState.growth.set()

@dp.message_handler(state=UserState.growth)
async def set_weight(message: types.Message, state: FSMContext):
    await state.update_data(growth=message.text)
    await message.answer('Введите свой вес:')
    await UserState.weight.set()

@dp.callback_query_handler(lambda call: call.data == 'product_buying')  # Обработчик для покупки продукта
async def send_confirm_message(call: types.CallbackQuery):
    await call.message.answer("Вы успешно приобрели продукт!")

@dp.message_handler(state=UserState.weight)
async def send_calories(message: types.Message, state: FSMContext):
    await state.update_data(weight=message.text)
    data = await state.get_data()

    age = int(data['age'])
    growth = int(data['growth'])
    weight = int(data['weight'])

    calories = 10 * weight + 6.25 * growth - 5 * age + 5

    await message.answer(f'Ваша норма калорий: {calories} kcal.')
    await state.finish()

@dp.message_handler(lambda message: message.text == 'Регистрация')
async def sing_up(message: types.Message):
    await message.answer("Введите имя пользователя (только латинский алфавит):")
    await RegistrationState.username.set()

@dp.message_handler(state=RegistrationState.username)
async def set_username(message: types.Message, state: FSMContext):
    username = message.text

    if is_included(username):
        await message.answer("Пользователь существует, введите другое имя:")
        return  # Остаться в этом состоянии, ждать новое имя

    await state.update_data(username=username)
    await message.answer("Введите свой email:")
    await RegistrationState.email.set()

@dp.message_handler(state=RegistrationState.email)
async def set_email(message: types.Message, state: FSMContext):
    email = message.text
    await state.update_data(email=email)
    await message.answer("Введите свой возраст:")
    await RegistrationState.age.set()

@dp.message_handler(state=RegistrationState.age)
async def set_age(message: types.Message, state: FSMContext):
    age = message.text

    data = await state.get_data()
    username = data['username']
    email = data['email']

    add_user(username, email, age)  # Добавление пользователя в БД
    await message.answer("Регистрация прошла успешно!")
    await state.finish()

# Обработчик всех остальных сообщений
@dp.message_handler(lambda message: True)
async def all_messages(message: types.Message):
    await message.answer("Введите команду /start, чтобы начать общение.")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)