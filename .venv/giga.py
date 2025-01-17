from imports_all import *

from config import gigachat_key


async def save_message_to_db(user_id: int, role: str, message: str):
    message_content = message.text if hasattr(message, 'text') else str(message)

    async with aiosqlite.connect("history.db") as db:
        await db.execute(
            """
            INSERT INTO history (id, role, message, timestamp)
            VALUES (?, ?, ?, ?)
            """,
            (user_id, role, message_content, datetime.now()),
        )
        await db.commit()


async def get_chat_history(user_id: int) -> str:
    async with aiosqlite.connect("history.db") as db:
        cursor = await db.execute(
            "SELECT role, message FROM history WHERE id = ? ORDER BY timestamp ASC",
            (user_id,),
        )
        rows = await cursor.fetchall()
        history = "\n".join([f"{role.capitalize()}: {message}" for role, message in rows])
        return history


async def chat_completion(id: int, prompt: str) -> str:
    llm = GigaChat(
        credentials=gigachat_key,
        model="GigaChat:latest",
        verify_ssl_certs=False
    )

    history = await get_chat_history(id)

    system_message = """
    Ты — помощник по сортировке мусора. Твоя задача — помочь пользователям сортировать отходы и правильно утилизировать различные материалы. 
    Ты можешь ответить на вопросы о том, какой мусор нужно класть в определенные контейнеры, как утилизировать опасные отходы, и дать рекомендации по экологичной жизни.


    Помни, что важно давать краткие, но точные ответы. Если вопрос неясен, спроси уточнение, чтобы помочь максимально эффективно.
    """

    prompt_template = f"""
    {system_message}
    История чата:
    {history}
    Вопрос:
    {prompt}
    """

    template = PromptTemplate(input_variables=["prompt"], template=prompt_template)
    chain = LLMChain(llm=llm, prompt=template)

    response = await chain.apredict(prompt=prompt)

    await save_message_to_db(id, "human", prompt)
    await save_message_to_db(id, "ai", response)

    return response

