import json
import os
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters
)
from config import BOT_TOKEN
from utils.storage import load_data, save_data
from utils.calculations import calculate_fuel
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackQueryHandler
from telegram import  WebAppInfo
# Путь к файлам с данными
CARS_FILE = "data/cars.json"
USERS_FILE = "data/users.json"

# Состояния для ConversationHandler
(
    WAITING_FOR_CAR_DATA,
    WAITING_FOR_CAR,
    WAITING_FOR_START_ODOMETER,
    WAITING_FOR_KM,
    WAITING_FOR_TRIP_DATA,
    WAITING_FOR_IDLE,
    WAITING_FOR_FUEL_START,
    WAITING_FOR_REFUEL
) = range(8)

# --- Утилиты ---
def is_valid_number(value):
    """Проверяет, является ли строка положительным числом (целым или вещественным)."""
    try:
        return float(value) >= 0
    except ValueError:
        return False

def load_data(file_path):
    """Загружает данные из JSON-файла."""
    if not os.path.exists(file_path):
        return {}
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)

def save_data(file_path, data):
    """Сохраняет данные в JSON-файл."""
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

# --- Функции команд ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Приветственное сообщение с кнопками."""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Добавить машину", callback_data="add_car")],
        [InlineKeyboardButton("Список машин", callback_data="list_car")],
        [InlineKeyboardButton("Просмотреть нормы", callback_data="view_car_menu")],
        [InlineKeyboardButton("Добавить поездку", callback_data="add_trip_menu")],
        [InlineKeyboardButton("Перейти в WebApp", web_app=WebAppInfo(url="https://pashasokorov1.github.io/fffggg/"))],
    ])
    # Отправляем сообщение с клавиатурой
    if update.message:
        await update.message.reply_text("Привет! Выберите действие:", reply_markup=keyboard)
    elif update.callback_query:
        await update.callback_query.edit_message_text("Привет! Выберите действие:", reply_markup=keyboard)



            
async def handle_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка нажатий кнопок главного меню."""
    query = update.callback_query
    await query.answer()

    if query.data == "add_car":
        # Очищаем user_data ТОЛЬКО если не идет процесс добавления поездки
        if "car_number" not in context.user_data:
            context.user_data.clear()

        context.user_data["waiting_for_car"] = True
        await query.edit_message_text("🚗 Введите данные машины в формате:\n<номер> <город> <трасса> <район> <простой>")
        return WAITING_FOR_CAR_DATA
    elif query.data == "list_car":
        await list_car_inline(update, context)
    elif query.data == "view_car_menu":
        await handle_view_car_menu(update, context)
    elif query.data == "add_trip_menu":
        await handle_add_trip_menu(update, context)
    elif query.data == "main_menu":
        await start(update, context)  # Возвращаем главное меню

async def list_car_inline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает список всех доступных машин через Inline-кнопки."""
    query = update.callback_query
    cars = load_data(CARS_FILE)

    if not cars:
        await query.edit_message_text("Список машин пуст. Добавьте машину сначала.")
        return

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(car_number, callback_data=f"view_car_{car_number}")]
        for car_number in cars.keys()
    ] + [[InlineKeyboardButton("Назад", callback_data="main_menu")]])

    await query.edit_message_text("Список машин:", reply_markup=keyboard)

async def handle_view_car_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Меню выбора машины для просмотра норм."""
    query = update.callback_query
    cars = load_data(CARS_FILE)

    if not cars:
        await query.edit_message_text("Список машин пуст. Добавьте машину сначала.")
        return

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(car_number, callback_data=f"view_car_{car_number}")]
        for car_number in cars.keys()
    ] + [[InlineKeyboardButton("Назад", callback_data="main_menu")]])

    await query.edit_message_text("Выберите машину для просмотра норм:", reply_markup=keyboard)



async def view_car_inline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает нормы для выбранной машины и добавляет кнопки 'Изменить нормы' и 'Удалить машину'."""
    query = update.callback_query
    car_number = query.data.replace("view_car_", "")
    cars = load_data(CARS_FILE)

    if car_number not in cars:
        await query.edit_message_text("❌ Ошибка: Машина не найдена.")
        return

    norms = cars[car_number]

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✏ Изменить нормы", callback_data=f"edit_norms_{car_number}")],
        [InlineKeyboardButton("❌ Удалить машину", callback_data=f"confirm_delete_{car_number}")],
        [InlineKeyboardButton("⬅ Назад", callback_data="view_car_menu")]
    ])

    await query.edit_message_text(
        f"🚗 **Нормы расхода топлива для {car_number}:**\n"
        f"🏙 Город: {norms['city']} л/100 км\n"
    f"🛣 Трасса: {norms['highway']} л/100 км\n"
    f"🌄 Район: {norms['district']} л/100 км\n"
    f"⏳ Простой: {norms['idle']} л/час",
        reply_markup=keyboard
    )

async def edit_norms_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Запрашивает у пользователя новые нормы расхода."""
    query = update.callback_query
    car_number = query.data.replace("edit_norms_", "")

    # ✅ Сохраняем номер машины в user_data
    context.user_data["edit_car_number"] = car_number

    await query.edit_message_text(
        f"✏ Введите новые нормы расхода для **{car_number}** в формате:\n"
        f"`<город> <трасса> <район> <простой>`\n\n"
        f"📌 Пример: `8.500 6.200 7.100 1.000`"
    )

async def handle_edit_norms_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает ввод новых норм и обновляет данные машины."""

    if "edit_car_number" not in context.user_data:
        return  # ⚠ НЕ ВЫДАЕМ ОШИБКУ, ПРОСТО НЕ ДЕЛАЕМ НИЧЕГО

    car_number = context.user_data["edit_car_number"]
    text = update.message.text.strip()
    args = text.split()

    if len(args) != 4:
        await update.message.reply_text(
            "🚨 Ошибка: Введите новые нормы расхода в формате:\n"
            "`<город> <трасса> <район> <простой>`\n"
            "📌 Пример: `8.500 6.200 7.100 1.000`"
        )
        return

    city_norm, highway_norm, district_norm, idle_norm = args

    if not all(is_valid_number(x) for x in [city_norm, highway_norm, district_norm, idle_norm]):
        await update.message.reply_text("🚨 Ошибка: Нормы расхода должны быть числовыми значениями.")
        return

    cars = load_data(CARS_FILE)

    if car_number not in cars:
        await update.message.reply_text("❌ Ошибка: Машина не найдена в базе. Попробуйте снова.")
        return ConversationHandler.END

    cars[car_number]["city"] = city_norm.strip()
    cars[car_number]["highway"] = highway_norm.strip()
    cars[car_number]["district"] = district_norm.strip()
    cars[car_number]["idle"] = idle_norm.strip()
    save_data(CARS_FILE, cars)

# ✅ Очищаем `edit_car_number` из user_data, чтобы избежать проблем в будущем
    del context.user_data["edit_car_number"]

    await update.message.reply_text(
        f"✅ **Нормы для {car_number} успешно обновлены!**\n"
        f"🏙 Город: {cars[car_number]['city']} л/100 км\n"
        f"🛣 Трасса: {cars[car_number]['highway']} л/100 км\n"
        f"🌄 Район: {cars[car_number]['district']} л/100 км\n"
        f"⏳ Простой: {cars[car_number]['idle']} л/час",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🚗 Добавить поездку", callback_data=f"add_trip_{car_number}")],
            [InlineKeyboardButton("⬅ Назад к машине", callback_data=f"view_car_{car_number}")],
            [InlineKeyboardButton("🔙 В главное меню", callback_data="main_menu")]
        ])
    )

    return ConversationHandler.END


async def confirm_delete_car(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Подтверждение удаления машины."""
    query = update.callback_query
    car_number = query.data.replace("confirm_delete_", "")

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Да, удалить", callback_data=f"delete_car_{car_number}")],
        [InlineKeyboardButton("❌ Отмена", callback_data=f"view_car_{car_number}")]
    ])

    await query.edit_message_text(
        f"⚠ Вы уверены, что хотите удалить машину **{car_number}**?",
        reply_markup=keyboard
    )


async def delete_car(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Удаляет выбранную машину и возвращает в меню выбора машин."""
    query = update.callback_query
    car_number = query.data.replace("delete_car_", "")

    cars = load_data(CARS_FILE)
    if car_number not in cars:
        await query.edit_message_text("❌ Ошибка: Машина не найдена.")
        return

    del cars[car_number]  # Удаляем машину
    save_data(CARS_FILE, cars)

    await query.edit_message_text(
        f"✅ Машина **{car_number}** успешно удалена!",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅ Назад к списку", callback_data="view_car_menu")]])
    )

    
async def handle_add_trip_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Меню выбора машины для добавления поездки."""
    query = update.callback_query
    await query.answer()  # Подтверждаем нажатие кнопки

    cars = load_data(CARS_FILE)
    if not cars:  # Если нет машин
        await query.edit_message_text("❌ Ошибка: Список машин пуст. Добавьте машину сначала.")
        return

    # Создаем кнопки с номерами машин
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(car_number, callback_data=f"add_trip_{car_number}")]
        for car_number in cars.keys()
    ] + [[InlineKeyboardButton("⬅ Назад", callback_data="main_menu")]])

    await query.edit_message_text("🚗 Выберите машину для добавления поездки:", reply_markup=keyboard)

async def handle_add_car_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает ввод данных машины и сохраняет её."""
    
    # Проверяем, не обрабатывается ли другая команда (например, добавление поездки)
    if "waiting_for_car" not in context.user_data:
        return
    
    text = update.message.text.strip()
    args = text.split()

    if len(args) != 5:
        await update.message.reply_text(
            "🚨 Ошибка: введите данные в формате:\n"
            "<номер> <город> <трасса> <район> <простой>\n"
            "📌 Пример: `А123ВМ 8.5 6.2 7.1 1.0`"
        )
        return WAITING_FOR_CAR_DATA

    car_number, city_norm, highway_norm, district_norm, idle_norm = args

    # Проверяем, что все введенные данные - числа
    if not all(is_valid_number(x) for x in [city_norm, highway_norm, district_norm, idle_norm]):
        await update.message.reply_text("🚨 Ошибка: нормы расхода должны быть положительными числами.")
        return WAITING_FOR_CAR_DATA

    cars = load_data(CARS_FILE)

    if car_number in cars:
        await update.message.reply_text(
            f"⚠ Машина с номером {car_number} уже существует!",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 В главное меню", callback_data="main_menu")]])
        )
        return ConversationHandler.END

    # Конвертация значений в числа с сохранением 3 знаков после запятой
    cars[car_number] = {
    "city": city_norm.strip(),    # Храним как строку
    "highway": highway_norm.strip(),
    "district": district_norm.strip(),
    "idle": idle_norm.strip(),
}

    # Добавляем машину в базу
    cars[car_number] = {
        "city": str(city_norm),
        "highway": str(highway_norm),
        "district": str(district_norm),
        "idle": str(idle_norm),
    }
    save_data(CARS_FILE, cars)

    # Очищаем все данные пользователя
    context.user_data.clear()

    # Отправляем сообщение с детальными расчётами
    await update.message.reply_text(
        f"✅ **Машина {car_number} успешно добавлена!**\n"
        f"📊 **Установленные нормы расхода:**\n"
        f" - 🏙 Город: {city_norm} л/100 км\n"
        f" - 🛣 Трасса: {highway_norm} л/100 км\n"
        f" - 🌄 Район: {district_norm} л/100 км\n"
        f" - ⏳ Простой: {idle_norm} л/час"
        f"\n🔢 **Как рассчитывается расход:**\n"
        f" - (Пройденный путь в км) × (Норма расхода на 100 км) ÷ 100\n"
        f" - (Часы простоя) × (Норма расхода в час)\n"
        f"\n🔙 Используйте команду `/list_car` для просмотра списка машин.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 В главное меню", callback_data="main_menu")]])
    )

    return ConversationHandler.END



async def add_trip_inline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начинает процесс добавления поездки."""
    query = update.callback_query
    await query.answer()

    car_number = query.data.replace("add_trip_", "")

    cars = load_data(CARS_FILE)

    if car_number not in cars:
        await query.edit_message_text("🚨 Ошибка: Машина не найдена. Начните заново.")
        return ConversationHandler.END

    # **Сохраняем `car_number` в контексте**
    context.user_data["car_number"] = car_number  # ✅ Теперь `car_number` не теряется

    await query.edit_message_text(
        f"🚗 **Начинаем добавление поездки для {car_number}**.\n\n"
        "📍 Введите начальное значение спидометра (км):"
    )

    return WAITING_FOR_START_ODOMETER

# --- Обработчики для добавления поездки ---
async def add_trip_start_odometer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохраняет начальный спидометр и запрашивает, сколько километров проехали."""

    if "car_number" not in context.user_data:
        await update.message.reply_text("🚨 Ошибка: Машина не найдена. Попробуйте снова.")
        return ConversationHandler.END

    if not update.message or not update.message.text:
        await update.message.reply_text("❌ Ошибка: Введите число.")
        return WAITING_FOR_START_ODOMETER

    start_odometer = update.message.text.strip()
    
    if not is_valid_number(start_odometer):
        await update.message.reply_text("🚨 Ошибка: Введите корректное число.")
        return WAITING_FOR_START_ODOMETER

    context.user_data["start_odometer"] = float(start_odometer)
    
    await update.message.reply_text("📏 Сколько километров вы проехали за день?")
    
    return WAITING_FOR_KM

async def add_trip_km(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохраняет километры и запрашивает их распределение."""
    
    # Проверяем, что бот НЕ ждет данных о машине
    if "waiting_for_car" in context.user_data:
        return

    km = update.message.text.strip()
    
    if not is_valid_number(km):
        await update.message.reply_text("🚨 Ошибка: Введите корректное количество километров.")
        return WAITING_FOR_KM

    km = update.message.text.strip()
    
    if not is_valid_number(km):
        await update.message.reply_text("🚨 Ошибка: Введите корректное количество километров.")
        return WAITING_FOR_KM

    # Проверяем, есть ли машина в контексте
    if "car_number" not in context.user_data:
        await update.message.reply_text("🚨 Ошибка: Машина не найдена. Начните заново.")
        return ConversationHandler.END  # Завершаем процесс

    context.user_data["km"] = float(km)

    await update.message.reply_text(
        "📊 Укажите, сколько км проехали в формате: `<город> <трасса> <район>`."
    )
    return WAITING_FOR_TRIP_DATA

async def add_trip_distribution(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохраняет распределение километров и запрашивает простой."""
    
    if "car_number" not in context.user_data:
        await update.message.reply_text("🚨 Ошибка: Машина не найдена. Начните заново.")
        return ConversationHandler.END  # Завершаем процесс

    trip_data = update.message.text.split()
    if len(trip_data) != 3 or not all(is_valid_number(x) for x in trip_data):
        await update.message.reply_text(
            "❌ Ошибка: Введите данные в формате: `<город> <трасса> <район>` (в км)."
        )
        return WAITING_FOR_TRIP_DATA

    city, highway, district = map(float, trip_data)
    
    if abs(city + highway + district - context.user_data["km"]) > 0.01:
        await update.message.reply_text(
            "❌ Ошибка: Сумма введённых километров должна равняться общему количеству пройденных."
        )
        return WAITING_FOR_TRIP_DATA

    context.user_data.update({"city": city, "highway": highway, "district": district})
    
    await update.message.reply_text("⏳ Введите количество часов простоя:")
    return WAITING_FOR_IDLE

async def add_trip_idle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохраняет простой и запрашивает топливо на начало."""
    idle = update.message.text
    if not is_valid_number(idle):
        await update.message.reply_text("Введите корректное количество часов.")
        return WAITING_FOR_IDLE

    context.user_data["idle"] = float(idle)
    await update.message.reply_text("Введите количество топлива в баке на начало дня.")
    return WAITING_FOR_FUEL_START

async def add_trip_fuel_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохраняет топливо на начало и запрашивает заправку."""
    fuel_start = update.message.text
    if not is_valid_number(fuel_start):
        await update.message.reply_text("Введите корректное количество топлива.")
        return WAITING_FOR_FUEL_START

    context.user_data["fuel_start"] = float(fuel_start)
    await update.message.reply_text("Введите количество заправленного топлива.")
    return WAITING_FOR_REFUEL

async def add_trip_refuel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохраняет заправку и завершает ввод данных."""
    refuel = update.message.text.strip()
    
    # Проверяем корректность введенного топлива
    if not is_valid_number(refuel):
        await update.message.reply_text("🚨 Ошибка: Введите корректное количество топлива.")
        return WAITING_FOR_REFUEL

    # ✅ Сохраняем точное значение без округления
    context.user_data["refuel"] = refuel

    # ✅ Проверяем, что все ключи есть в user_data
    required_keys = ["car_number", "start_odometer", "km", "city", "highway", "district", "idle", "fuel_start", "refuel"]
    missing_keys = [key for key in required_keys if key not in context.user_data]

    if missing_keys:
        await update.message.reply_text(f"❌ Ошибка: Отсутствуют данные ({', '.join(missing_keys)}). Начните заново.")
        return ConversationHandler.END

    # ✅ Загружаем данные из user_data
    car_number = context.user_data["car_number"]
    start_odometer = context.user_data["start_odometer"]
    km = context.user_data["km"]
    city = context.user_data["city"]
    highway = context.user_data["highway"]
    district = context.user_data["district"]
    idle = context.user_data["idle"]
    fuel_start = context.user_data["fuel_start"]
    refuel = context.user_data["refuel"]

    # ✅ Проверяем, есть ли машина в базе
    cars = load_data(CARS_FILE)
    if car_number not in cars:
        await update.message.reply_text("❌ Ошибка: Машина не найдена в базе.")
        return ConversationHandler.END

    # ✅ Получаем нормы расхода
    norms = cars[car_number]
    if not all(key in norms for key in ["city", "highway", "district", "idle"]):
        await update.message.reply_text("❌ Ошибка: Нормы расхода для машины некорректны.")
        return ConversationHandler.END

    # ✅ Выполняем расчёт расхода топлива
    result = calculate_fuel(city, highway, district, idle, norms)
    total_fuel = result["total_fuel"]
    fuel_end = float(fuel_start) + float(refuel) - float(total_fuel)
    end_odometer = float(start_odometer) + float(km)

    # ✅ Загружаем данные пользователей
    users = load_data(USERS_FILE)
    user_id = str(update.effective_user.id)

    # ✅ Создаём запись о поездке
    if user_id not in users:
        users[user_id] = {"trips": []}

    users[user_id]["trips"].append({
        "car": car_number,
        "start_odometer": start_odometer,
        "end_odometer": end_odometer,
        "km": km,
        "city": city,
        "highway": highway,
        "district": district,
        "idle": idle,
        "fuel_start": fuel_start,
        "refuel": refuel,
        "fuel_end": fuel_end,
        "total_fuel": total_fuel,
    })
    save_data(USERS_FILE, users)

    # ✅ Очищаем user_data, чтобы не было лишних данных
    context.user_data.clear()

    # ✅ Отправляем сообщение с результатами
    await update.message.reply_text(
        f"✅ **Расчёты завершены!**\n"
        f"📍 **Спидометр:** {start_odometer} км → {end_odometer} км\n"
        f"📊 **Подробные расчёты:**\n"
        f"🏙 Город: {city} км × {norms['city']} л/100 км = {result['city_fuel']} л\n"
        f"🛣 Трасса: {highway} км × {norms['highway']} л/100 км = {result['highway_fuel']} л\n"
        f"🌄 Район: {district} км × {norms['district']} л/100 км = {result['district_fuel']} л\n"
        f"⏳ Простой: {idle} ч × {norms['idle']} л/ч = {result['idle_fuel']} л\n"
        f"\n💡 **Общий расход:**\n"
        f"🔹 {result['city_fuel']} + {result['highway_fuel']} + {result['district_fuel']} + {result['idle_fuel']} = {result['total_fuel']} л\n\n"
        f"⛽ **Баланс топлива:**\n"
        f"🔹 Начало дня: {fuel_start} л\n"
        f"🔹 Заправлено: {refuel} л\n"
        f"🔹 Потрачено: {total_fuel} л\n"
        f"🔹 Остаток: {fuel_start} + {refuel} - {total_fuel} = {fuel_end} л",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 В главное меню", callback_data="main_menu")],
            [InlineKeyboardButton("🚗 Добавить ещё поездку", callback_data=f"add_trip_{car_number}")]
        ])
    )
    
    return ConversationHandler.END

# --- Главная функция ---
def main():
    """Запуск бота."""
    application = Application.builder().token(BOT_TOKEN).build()

    # Обработчик команды /start
    application.add_handler(CommandHandler("start", start))

    # Обработчик кнопок главного меню (без main_menu)
    application.add_handler(CallbackQueryHandler(handle_menu_callback, pattern="^(add_car|list_car|view_car_menu|add_trip_menu|delete_car_menu)$"))

    # Отдельный обработчик для главного меню
    application.add_handler(CallbackQueryHandler(start, pattern="^main_menu$"))

    # Обработчики для конкретных функций
    application.add_handler(CallbackQueryHandler(view_car_inline, pattern="^view_car_"))
    application.add_handler(CallbackQueryHandler(handle_add_trip_menu, pattern="^add_trip_menu$"))
    application.add_handler(CallbackQueryHandler(list_car_inline, pattern="^list_car$"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_add_car_data), group=1)
    application.add_handler(CallbackQueryHandler(confirm_delete_car, pattern="^confirm_delete_"))
    application.add_handler(CallbackQueryHandler(delete_car, pattern="^delete_car_"))
    application.add_handler(CallbackQueryHandler(edit_norms_request, pattern="^edit_norms_"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_edit_norms_input), group=2)

    car_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(handle_menu_callback, pattern="^add_car$")],
        states={
            WAITING_FOR_CAR_DATA: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_add_car_data)],
        },
        fallbacks=[CallbackQueryHandler(start, pattern="^main_menu$")],  # Возвращаемся в главное меню
        per_user=True,
        per_chat=False,
    )

    application.add_handler(car_handler)

    
    # ConversationHandler для добавления поездки
    trip_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_trip_inline, pattern="^add_trip_")],
        states={
            WAITING_FOR_START_ODOMETER: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_trip_start_odometer)],
            WAITING_FOR_KM: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_trip_km)],
            WAITING_FOR_TRIP_DATA: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_trip_distribution)],
            WAITING_FOR_IDLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_trip_idle)],
            WAITING_FOR_FUEL_START: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_trip_fuel_start)],
            WAITING_FOR_REFUEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_trip_refuel)],
        },
        fallbacks=[CallbackQueryHandler(start, pattern="^main_menu$")],  # Возвращаемся в главное меню
        per_user=True,
        per_chat=False,
    )
    application.add_handler(trip_handler)
    # Запуск бота
    application.run_polling()

if __name__ == "__main__":
    main()