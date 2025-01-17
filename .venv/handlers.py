from imports_all import *

from BD import Registry
from giga import chat_completion

router = Router()

async def send_msg(bot: Bot):
    async with (aiosqlite.connect('users.db') as db):
        async with db.execute("SELECT id FROM users WHERE statusrem=TRUE") as cursor:
            rows = await cursor.fetchall()
            if rows:
                text = 'Интересный совет:\n' + await chat_completion(0, 'Дай краткий необычный совет по утилизации мусора')
                for row in rows:
                    try:
                        await bot.send_message(chat_id=row[0], text=text)
                    except Exception as e:
                        logging.info(f"Ошибка при отправке сообщения пользователю {row[0]}: {e}")


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    async with aiosqlite.connect('users.db') as db:
        async with db.execute("SELECT id FROM users WHERE id = ?",
                              (message.from_user.id,)) as cursor:
            if await cursor.fetchone() is None:
                await state.set_state(Registry.name)
                await message.answer('Введите Ваше имя')
            else:
                await message.answer(f'Вы уже зарегестрированы!')

@router.message(Registry.name)
async def reg_surname(message:Message, state: FSMContext):
    name = message.text
    if bool(re.match(r'^[A-Za-zА-Яа-яЁё\s-]+$', name)):
        await state.update_data(name=name)
        await state.set_state(Registry.surname)
        await message.answer('Введите Вашу фамилию')
    else:
        await message.answer('Пожалуйста, введите корректное имя (только буквы, пробелы или дефис).')
        await cmd_start(message)


@router.message(Registry.surname)
async def reg_end(message:Message, state: FSMContext):
    surname = message.text
    if bool(re.match(r'^[A-Za-zА-Яа-яЁё\s-]+$', surname)):
        await state.update_data(surname=message.text)
        data = await state.get_data()
        await state.clear()

        async with aiosqlite.connect('users.db') as db:
            await db.execute('''
                              INSERT INTO users (id, statusrem, name, surname) 
                              VALUES (?, ?, ?, ?)
                          ''', (message.from_user.id, False, data['name'], data['surname']))
            await db.commit()
        await message.answer(f'Регистрация завершена!\n'
                            f'Вас зовут: {data["name"]} {data["surname"]}\n'
                            f'Ваш id: {message.from_user.id}')
        await cmd_help(message)
    else:
        await message.answer('Пожалуйста, введите корректную фамилию (только буквы, пробелы или дефис).')
        await reg_surname(message)


@router.message(Command("menu"))
async def cmd_menu(message: Message):
    kb_list = [
        [InlineKeyboardButton(text="ℹ️ Помощь", callback_data="help")],
        [InlineKeyboardButton(text="♻️ Информация", callback_data="info")],
        [InlineKeyboardButton(text="✅ Подписаться на рассылку", callback_data="subscribe")],
        [InlineKeyboardButton(text="🚫 Отписаться от рассылки", callback_data="unsubscribe")],
        [InlineKeyboardButton(text="🎯 Викторина", callback_data="quiz")],
        [InlineKeyboardButton(text="💬 Включить чат с экспертом", callback_data="start_chat")],
        [InlineKeyboardButton(text="🔇 Выключить чат с экспертом", callback_data="stop_chat")]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=kb_list)
    await message.answer("Выберите команду из меню:", reply_markup=keyboard)



@router.callback_query(F.data=='start_chat')
async def start_chat(callback: CallbackQuery, state: State):
    await state.set_state(Registry.start_chat)
    await callback.answer('')
    await callback.message.answer('💬 Включен режим чата с ИИ. Задавайте свои вопросы по сортировке мусора! ♻️')

@router.message(Command("start_chat"))
async def start_chat(message:Message, state: FSMContext):
    await state.set_state(Registry.start_chat)
    await message.answer('💬 Включен режим чата с ИИ. Задавайте свои вопросы по сортировке мусора! ♻️')

@router.callback_query(F.data=='stop_chat')
async def stop_chat (callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer('')
    await callback.message.answer('🔕 Выключен режим чата с ИИ. Возвращайтесь, когда будут вопросы! ♻️')

@router.message(Command("stop_chat"))
async def stop_chat (message:Message, state: FSMContext):
    await state.clear()
    await message.answer('🔕 Выключен режим чата с ИИ. Возвращайтесь, когда будут вопросы! ♻️')


@router.message(Command("subscribe"))
async def ontext(message: Message):
    id = message.from_user.id
    async with aiosqlite.connect("users.db") as db:
      await db.execute("UPDATE users SET statusrem = TRUE WHERE id = ?", (id, ))
      await db.commit()
      await message.answer('⏰ Напоминания активированы! Теперь вы будете получать полезные советы по сортировке мусора. ♻️')


@router.callback_query(F.data=='subscribe')
async def ontext(callback: CallbackQuery):
    id = callback.from_user.id
    async with aiosqlite.connect("users.db") as db:
      await db.execute("UPDATE users SET statusrem = TRUE WHERE id = ?", (id, ))
      await db.commit()
    await callback.message.answer('⏰ Напоминания активированы! Теперь вы будете получать полезные советы по сортировке мусора. ♻️')
    await callback.answer()

@router.message(Command("unsubscribe"))
async def offtext(message: Message):
    id = message.from_user.id
    async with aiosqlite.connect("users.db") as db:
        await db.execute("UPDATE users SET statusrem = FALSE WHERE id = ?", (id, ))
        await db.commit()
    await message.answer('🔕 Напоминания отключены! Вы всегда можете включить их снова, если потребуется. ♻️')


@router.callback_query(F.data=="unsubscribe")
async def offtext(callback: CallbackQuery):
    id = callback.from_user.id
    async with aiosqlite.connect("users.db") as db:
        await db.execute("UPDATE users SET statusrem = FALSE WHERE id = ?", (id, ))
        await db.commit()
    await callback.message.answer('🔕 Напоминания отключены! Вы всегда можете включить их снова, если потребуется. ♻️')
    await callback.answer('')

help_text = (
    "Помощь по боту 🤖:\n"
    "📌 /start - Регистрация.\n"
    "📋 /menu - Открывает меню с командами.\n"
    "♻️ /info - Информация о сортировке мусора.\n"
    "🎯 /quiz - Викторина для проверки знаний.\n"
    "✅ /subscribe - Включает рассылку советов.\n"
    "🚫 /unsubscribe - Выключает рассылку советов.\n"
    "💬 /start_chat - Включить мод общения с экспертом по сортировке мусора.\n"
    "🔇 /stop_chat - Выключить мод общения с экспертом по сортировке мусора.\n"
)

@router.callback_query(F.data == "help")
async def cmd_help(callback: CallbackQuery):
    await callback.answer('')
    await callback.message.answer(help_text)

@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(help_text)


info_text = (
    "📘 Краткая информация о сортировке мусора:\n"
    "1. Пластик (PET, HDPE) - отправляйте в соответствующие контейнеры.\n"
    "2. Бумага - сдавайте чистую и сухую.\n"
    "3. Стекло - обязательно очищайте перед утилизацией.\n"
    "4. Металл - сдавайте алюминиевые и жестяные банки в контейнеры для металла.\n"
    "5. Органические отходы - компостируйте, если это возможно.\n"
    "6. Опасные отходы (батарейки, лампы) - сдавайте в специализированные пункты приема.\n"
    "7. Текстиль - сдавайте ненужную одежду в пункты переработки текстиля.\n"
    "\n🔍 Полную информацию Уточняйте в вашем регионе, так как правила могут отличаться."
)


@router.message(Command("info"))
async def cmd_info(message: Message):
    await message.answer(info_text)

@router.callback_query(F.data == "info")
async def cmd_info(callback: CallbackQuery):
    callback.answer('')
    await callback.message.answer(info_text)


@router.message(Command("quiz"))
async def cmd_quiz(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Да", callback_data="quiz_yes")],
        [InlineKeyboardButton(text="Нет", callback_data="quiz_no")]
    ])
    await message.answer("♻️ Вопрос 1: Можно ли выбрасывать батарейки в обычный мусор?", reply_markup=keyboard)


@router.callback_query(F.data=="quiz")
async def cmd_quiz(callback: CallbackQuery):
    await callback.answer('')
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Да", callback_data="quiz_yes")],
        [InlineKeyboardButton(text="Нет", callback_data="quiz_no")]
    ])
    await callback.message.answer("♻️ Вопрос 1: Можно ли выбрасывать батарейки в обычный мусор?", reply_markup=keyboard)


@router.callback_query(F.data == "quiz_yes")
async def quiz_yes(callback: CallbackQuery):
    await callback.answer("❌ Неверно! Батарейки нужно сдавать в специальные пункты.", show_alert=True)
    await callback.message.answer("Попробуйте ещё раз или прочитайте раздел 'Информация о сортировке мусора'. 📘")


@router.callback_query(F.data == "quiz_no")
async def quiz_no(callback: CallbackQuery):
    await callback.answer("✅ Верно! Батарейки нужно сдавать в специальные пункты.", show_alert=True)
    await callback.message.answer("Молодец! Вы отлично разбираетесь в утилизации мусора. 🌍")
    await cmd_quiz_2(callback.message)


@router.callback_query(F.data == "quiz_2")
async def cmd_quiz_2(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Да", callback_data="quiz_2_yes")],
        [InlineKeyboardButton(text="Нет", callback_data="quiz_2_no")]
    ])
    await message.answer("📝 Вопрос 2: Можно ли выбрасывать стекло в контейнер для пластика?", reply_markup=keyboard)


@router.callback_query(F.data == "quiz_2_yes")
async def quiz_2_yes(callback: CallbackQuery):
    await callback.answer("❌ Неверно! Стекло должно выбрасываться в контейнер для стекла.", show_alert=True)
    await callback.message.answer("Попробуйте ещё раз или прочитайте раздел 'Информация о сортировке мусора'. 📘")


@router.callback_query(F.data == "quiz_2_no")
async def quiz_2_no(callback: CallbackQuery):
    await callback.answer("✅ Верно! Стекло должно выбрасываться в контейнер для стекла.", show_alert=True)
    await callback.message.answer("Отлично! У вас хорошее знание сортировки. 🌍")
    await cmd_quiz_3(callback.message)

@router.callback_query(F.data == "quiz_3")
async def cmd_quiz_3(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Да", callback_data="quiz_3_yes")],
        [InlineKeyboardButton(text="Нет", callback_data="quiz_3_no")]
    ])
    await message.answer("🧻 Вопрос 3: Можно ли сдавать грязную бумагу на переработку?", reply_markup=keyboard)


@router.callback_query(F.data == "quiz_3_yes")
async def quiz_3_yes(callback: CallbackQuery):
    await callback.answer("❌ Неверно! Бумага должна быть чистой и сухой для переработки.", show_alert=True)
    await callback.message.answer("Попробуйте ещё раз или прочитайте раздел 'Информация о сортировке мусора'. 📘")


@router.callback_query(F.data == "quiz_3_no")
async def quiz_3_no(callback: CallbackQuery):
    await callback.answer("✅ Верно! Бумага должна быть чистой и сухой для переработки.", show_alert=True)
    await callback.message.answer("Отлично! Вы все больше разобрались в сортировке мусора. 🌍")
    await cmd_quiz_4(callback.message)

@router.callback_query(F.data == "quiz_4")
async def cmd_quiz_4(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Да", callback_data="quiz_4_yes")],
        [InlineKeyboardButton(text="Нет", callback_data="quiz_4_no")]
    ])
    await message.answer("🛢️ Вопрос 4: Можно ли выбрасывать моторное масло в обычный контейнер для отходов?", reply_markup=keyboard)


@router.callback_query(F.data == "quiz_4_yes")
async def quiz_4_yes(callback: CallbackQuery):
    await callback.answer("❌ Неверно! Моторное масло должно утилизироваться в специализированных пунктах.", show_alert=True)
    await callback.message.answer("Попробуйте ещё раз или прочитайте раздел 'Информация о сортировке мусора'. 📘")


@router.callback_query(F.data == "quiz_4_no")
async def quiz_4_no(callback: CallbackQuery):
    await callback.answer("✅ Верно! Моторное масло должно утилизироваться в специализированных пунктах.", show_alert=True)
    await callback.message.answer("Молодец! Вы действительно хорошо разбираетесь в утилизации мусора. 🌍")


@router.message(Registry.start_chat)
async def chat_gigachat(message: Message):
    id = message.from_user.id
    response = await chat_completion(id, message.text)
    await message.answer(response, parse_mode=ParseMode.MARKDOWN)


async def set_commands(bot):
    commands = [
        BotCommand(command="help", description="ℹ️ Показать помощь"),
        BotCommand(command="menu", description="🍔 Открыть меню"),
        BotCommand(command="info", description="♻️ Информация о сортировке мусора"),
        BotCommand(command="quiz", description="🎯 Начать викторину"),
        BotCommand(command="subscribe", description="✅ Подписаться на рассылку советов"),
        BotCommand(command="unsubscribe", description="🚫 Отписаться от рассылки советов"),
        BotCommand(command="start_chat", description="💬 Включить общение с ИИ-помощником"),
        BotCommand(command="stop_chat", description="🔕 Выключить общение с ИИ-помощником")
    ]
    await bot.set_my_commands(commands, scope=BotCommandScopeDefault())


@router.message()
async def prtext(message: Message):
    await message.answer("Я не понимаю эту команду. Напишите /help для получения списка команд.")

