from imports_all import *


class Registry(StatesGroup):
    name = State()
    surname = State()
    start_chat = State()

async def start_db():
    async with aiosqlite.connect('users.db') as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                statusrem BOOLEAN,
                name TEXT,
                surname TEXT
                giga_history TEXT
            )
        ''')
        await db.commit()

    async with aiosqlite.connect('history.db') as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER,
                role TEXT,
                message TEXT,
                timestamp DATETIME
            )
        ''')
        await db.commit()


class SomeMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any]
    ) -> Any:
        if data['event_update'].message.text == '/start':
            return await handler(event, data)

        id = data['event_update'].message.chat.id
        state: FSMContext = data['state']

        current_state = await state.get_state()

        if current_state not in [Registry.name.state, Registry.surname.state]:
            async with aiosqlite.connect('users.db') as db:
                async with db.execute("SELECT id FROM users WHERE id = ?", (id,)) as cursor:
                    if await cursor.fetchone() is None:
                        await data['event_update'].message.answer(
                            'Вы не зарегистрированы! Зарегистрируйтесь, используя команду /start.'
                        )
                        return

        return await handler(event, data)
