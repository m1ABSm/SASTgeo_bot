import os
import json
import logging
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# Загрузка переменных окружения
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID'))

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Загрузка базы данных
def load_db():
    try:
        with open('database.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "users": [],
            "assistants": [],
            "tasks": [],
            "tests": []
        }

# Сохранение базы данных
def save_db(db):
    with open('database.json', 'w') as f:
        json.dump(db, f, indent=4)

# Определение роли пользователя
def get_role(update: Update):
    user_id = update.effective_user.id
    username = update.effective_user.username
    db = load_db()
    for user in db['users']:
        if user['id'] == str(user_id) or user['name'] == username:
            return user['role']
    for assistant in db['assistants']:
        if assistant['id'] == str(user_id) or assistant['name'] == username:
            return assistant['role']
    if user_id == ADMIN_ID:
        return 'admin'
    return None

# Отправка сообщения или редактирование существующего сообщения
async def send_or_edit_message(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, reply_markup: InlineKeyboardMarkup):
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, reply_markup=reply_markup)

# Команды
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    role = get_role(update)
    if role == 'admin':
        await admin_menu(update, context)
    elif role == 'assistant':
        await assistant_menu(update, context)
    elif role == 'user':
        await user_menu(update, context)
    else:
        await update.message.reply_text("Вы не зарегистрированы. Введите номер студенческого билета:")
        context.user_data['registration_step'] = 'student_id'

async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Ассистент", callback_data='admin_assistant')],
        [InlineKeyboardButton("Студенты", callback_data='admin_students')],
        [InlineKeyboardButton("Задания", callback_data='admin_tasks')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await send_or_edit_message(update, context, 'Меню администратора:', reply_markup)

async def assistant_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Студенты", callback_data='assistant_students')],
        [InlineKeyboardButton("Задания", callback_data='assistant_tasks')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await send_or_edit_message(update, context, 'Меню ассистента:', reply_markup)

async def user_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Мои задания", callback_data='user_tasks')],
        [InlineKeyboardButton("Мои тесты", callback_data='user_tests')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await send_or_edit_message(update, context, 'Меню пользователя:', reply_markup)

# Обработка нажатий на кнопки
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == 'admin_assistant':
        await admin_assistant_menu(update, context)
    elif data == 'admin_students':
        await admin_students_menu(update, context)
    elif data == 'admin_tasks':
        await admin_tasks_menu(update, context)
    elif data == 'assistant_students':
        await assistant_students_menu(update, context)
    elif data == 'assistant_tasks':
        await assistant_tasks_menu(update, context)
    elif data == 'user_tasks':
        await user_tasks_menu(update, context)
    elif data == 'user_tests':
        await user_tests_menu(update, context)
    elif data == 'back':
        role = get_role(update)
        if role == 'admin':
            await admin_menu(update, context)
        elif role == 'assistant':
            await assistant_menu(update, context)
        elif role == 'user':
            await user_menu(update, context)

async def admin_assistant_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Добавить ассистента", callback_data='add_assistant')],
        [InlineKeyboardButton("Удалить ассистента", callback_data='remove_assistant')],
        [InlineKeyboardButton("Назад", callback_data='back')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await send_or_edit_message(update, context, 'Меню ассистентов:', reply_markup)

async def add_assistant(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_or_edit_message(update, context, 'Введите @name ассистента:', InlineKeyboardMarkup([]))
    context.user_data['adding_assistant'] = 'name'

async def remove_assistant(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = load_db()
    assistants = db['assistants']
    if not assistants:
        await send_or_edit_message(update, context, 'Нет ассистентов для удаления.', InlineKeyboardMarkup([[InlineKeyboardButton("Назад", callback_data='back')]]))
        return
    keyboard = []
    for assistant in assistants:
        button_text = f"{assistant['position']} {assistant['fio']} ({assistant['name']})"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f'remove_{assistant["name"]}')])
    keyboard.append([InlineKeyboardButton("Назад", callback_data='back')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await send_or_edit_message(update, context, 'Выберите ассистента для удаления:', reply_markup)

async def admin_students_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = load_db()
    students = db['users']
    if not students:
        await send_or_edit_message(update, context, 'Нет студентов.', InlineKeyboardMarkup([[InlineKeyboardButton("Назад", callback_data='back')]]))
        return
    text = "Список студентов:\n"
    for student in students:
        text += f"{student['student_id']} {student['fio']} {student['group']}\n"
    keyboard = [
        [InlineKeyboardButton("Назад", callback_data='back')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await send_or_edit_message(update, context, text, reply_markup)

async def admin_tasks_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Добавить задание", callback_data='add_task')],
        [InlineKeyboardButton("Удалить задание", callback_data='remove_task')],
        [InlineKeyboardButton("Назад", callback_data='back')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await send_or_edit_message(update, context, 'Меню заданий:', reply_markup)

async def add_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Тест", callback_data='add_test')],
        [InlineKeyboardButton("Задание", callback_data='add_assignment')],
        [InlineKeyboardButton("Назад", callback_data='back')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await send_or_edit_message(update, context, 'Выберите тип задания:', reply_markup)

async def add_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_or_edit_message(update, context, 'Введите название теста:', InlineKeyboardMarkup([]))
    context.user_data['adding_test'] = 'title'

async def add_assignment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_or_edit_message(update, context, 'Введите название задания:', InlineKeyboardMarkup([]))
    context.user_data['adding_assignment'] = 'title'

async def remove_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = load_db()
    tasks = db['tasks']
    if not tasks:
        await send_or_edit_message(update, context, 'Нет заданий для удаления.', InlineKeyboardMarkup([[InlineKeyboardButton("Назад", callback_data='back')]]))
        return
    keyboard = []
    for task in tasks:
        button_text = task['title']
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f'remove_{task["title"]}')])
    keyboard.append([InlineKeyboardButton("Назад", callback_data='back')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await send_or_edit_message(update, context, 'Выберите задание для удаления:', reply_markup)

async def assistant_students_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await admin_students_menu(update, context)

async def assistant_tasks_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await admin_tasks_menu(update, context)

async def user_tasks_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = load_db()
    user_id = update.effective_user.id
    user = next((u for u in db['users'] if u['id'] == str(user_id)), None)
    if not user:
        await send_or_edit_message(update, context, 'Вы не зарегистрированы.', InlineKeyboardMarkup([]))
        return
    group = user['group']
    tasks = [t for t in db['tasks'] if group in t['groups']]
    if not tasks:
        await send_or_edit_message(update, context, 'У вас нет доступных заданий.', InlineKeyboardMarkup([[InlineKeyboardButton("Назад", callback_data='back')]]))
        return
    keyboard = []
    for task in tasks:
        button_text = task['title']
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f'task_{task["title"]}')])
    keyboard.append([InlineKeyboardButton("Назад", callback_data='back')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await send_or_edit_message(update, context, 'Мои задания:', reply_markup)

async def user_tests_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = load_db()
    user_id = update.effective_user.id
    user = next((u for u in db['users'] if u['id'] == str(user_id)), None)
    if not user:
        await send_or_edit_message(update, context, 'Вы не зарегистрированы.', InlineKeyboardMarkup([]))
        return
    group = user['group']
    tests = [t for t in db['tests'] if group in t['groups']]
    if not tests:
        await send_or_edit_message(update, context, 'У вас нет доступных тестов.', InlineKeyboardMarkup([[InlineKeyboardButton("Назад", callback_data='back')]]))
        return
    keyboard = []
    for test in tests:
        button_text = test['title']
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f'test_{test["title"]}')])
    keyboard.append([InlineKeyboardButton("Назад", callback_data='back')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await send_or_edit_message(update, context, 'Мои тесты:', reply_markup)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_data = context.user_data

    if 'registration_step' in user_data:
        if user_data['registration_step'] == 'student_id':
            user_data['student_id'] = text
            await update.message.reply_text("Введите ФИО:")
            user_data['registration_step'] = 'fio'
        elif user_data['registration_step'] == 'fio':
            user_data['fio'] = text
            user_id = update.effective_user.id
            username = update.effective_user.username
            group = ''.join(filter(str.isdigit, text))[0]  # Определение группы по первой цифре студенческого билета
            db = load_db()
            db['users'].append({"id": str(user_id), "name": username, "role": "user", "group": group, "student_id": user_data['student_id'], "fio": user_data['fio']})
            save_db(db)
            del user_data['registration_step']
            del user_data['student_id']
            del user_data['fio']
            await update.message.reply_text("Регистрация завершена.")
            await user_menu(update, context)
    elif 'adding_assistant' in user_data:
        if user_data['adding_assistant'] == 'name':
            user_data['assistant_name'] = text
            await update.message.reply_text("Введите должность:")
            user_data['adding_assistant'] = 'position'
        elif user_data['adding_assistant'] == 'position':
            user_data['assistant_position'] = text
            await update.message.reply_text("Введите ФИО:")
            user_data['adding_assistant'] = 'fio'
        elif user_data['adding_assistant'] == 'fio':
            user_data['assistant_fio'] = text
            assistant_name = user_data['assistant_name']
            assistant_position = user_data['assistant_position']
            assistant_fio = user_data['assistant_fio']
            db = load_db()
            db['assistants'].append({"id": "", "name": assistant_name, "role": "assistant", "position": assistant_position, "fio": assistant_fio})
            save_db(db)
            del user_data['assistant_name']
            del user_data['assistant_position']
            del user_data['assistant_fio']
            del user_data['adding_assistant']
            await update.message.reply_text("Ассистент добавлен.")
            await admin_assistant_menu(update, context)
    elif 'adding_test' in user_data:
        if user_data['adding_test'] == 'title':
            user_data['test_title'] = text
            await update.message.reply_text("Введите вопросы теста в формате:\nВопрос 1\nОтвет 1\nОтвет 2\n...\nВопрос 2\nОтвет 1\nОтвет 2\n...")
            user_data['adding_test'] = 'questions'
        elif user_data['adding_test'] == 'questions':
            test_title = user_data['test_title']
            test_questions = text.split('\n')
            test_data = {}
            i = 0
            while i < len(test_questions):
                question = test_questions[i]
                answers = []
                i += 1
                while i < len(test_questions) and not test_questions[i].startswith('Вопрос'):
                    answers.append(test_questions[i])
                    i += 1
                test_data[question] = answers
            file_path = f'tests/{test_title}.json'
            with open(file_path, 'w') as f:
                json.dump(test_data, f, indent=4)
            db = load_db()
            db['tests'].append({"title": test_title, "file_path": file_path, "groups": [], "results": {}})
            save_db(db)
            del user_data['test_title']
            del user_data['adding_test']
            await update.message.reply_text("Тест добавлен.")
            await admin_tasks_menu(update, context)
    elif 'adding_assignment' in user_data:
        if user_data['adding_assignment'] == 'title':
            user_data['task_title'] = text
            await update.message.reply_text("Введите задание:")
            user_data['adding_assignment'] = 'content'
        elif user_data['adding_assignment'] == 'content':
            task_title = user_data['task_title']
            task_content = update.message.text
            file_path = f'tasks/{task_title}.txt'
            with open(file_path, 'w') as f:
                f.write(task_content)
            db = load_db()
            db['tasks'].append({"title": task_title, "file_path": file_path, "groups": []})
            save_db(db)
            del user_data['task_title']
            del user_data['adding_assignment']
            await update.message.reply_text("Задание добавлено.")
            await admin_tasks_menu(update, context)

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith('remove_'):
        entity_name = data.split('_')[1]
        db = load_db()
        if data.startswith('remove_@'):
            assistants = db['assistants']
            assistants = [a for a in assistants if a['name'] != entity_name]
            db['assistants'] = assistants
            save_db(db)
            await send_or_edit_message(update, context, "Ассистент удален.", InlineKeyboardMarkup([[InlineKeyboardButton("Назад", callback_data='back')]]))
        elif data.startswith('remove_'):
            tasks = db['tasks']
            tasks = [t for t in tasks if t['title'] != entity_name]
            db['tasks'] = tasks
            save_db(db)
            await send_or_edit_message(update, context, "Задание удалено.", InlineKeyboardMarkup([[InlineKeyboardButton("Назад", callback_data='back')]]))
    elif data.startswith('task_'):
        task_title = data.split('_')[1]
        db = load_db()
        task = next((t for t in db['tasks'] if t['title'] == task_title), None)
        if task:
            with open(task['file_path'], 'r') as f:
                task_content = f.read()
            keyboard = [
                [InlineKeyboardButton("Назад", callback_data='back')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await send_or_edit_message(update, context, task_content, reply_markup)
    elif data.startswith('test_'):
        test_title = data.split('_')[1]
        db = load_db()
        test = next((t for t in db['tests'] if t['title'] == test_title), None)
        if test:
            with open(test['file_path'], 'r') as f:
                test_data = json.load(f)
            test_questions = "\n".join([f"{q}\n{', '.join(a)}" for q, a in test_data.items()])
            keyboard = [
                [InlineKeyboardButton("Назад", callback_data='back')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await send_or_edit_message(update, context, test_questions, reply_markup)

def main():
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    application.run_polling()

if __name__ == '__main__':
    main()