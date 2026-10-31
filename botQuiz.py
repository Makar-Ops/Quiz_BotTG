import asyncio
import logging
import sqlite3
import random
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder

TOKEN = "YOUR TOKEN HERE"
logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

def init_db():
    conn = sqlite3.connect('quiz.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS leaderboard 
                      (user_id INTEGER PRIMARY KEY, username TEXT, score INTEGER)''')
    conn.commit()
    conn.close()

init_db()

def get_random_questions():
    conn = sqlite3.connect('quiz.db')
    cursor = conn.cursor()

    cursor.execute("SELECT text, answer FROM questions ORDER BY RANDOM() LIMIT 30")
    data = cursor.fetchall()
    conn.close()

    questions = []
    for row in data:
        questions.append({"text": row[0], "answer": row[1]})
    return questions

class QuizStates(StatesGroup):
    playing = State()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.button(text="🎮 Начать квиз", callback_data="start_quiz")
    builder.button(text="🏆 Таблица лидеров", callback_data="show_top")
    
    await message.answer(
        f"Привет, {message.from_user.first_name}! Готов проверить свой IQ?", 
        reply_markup=builder.as_markup()
    )

@dp.callback_query(F.data == "show_top")
async def show_top(callback: types.CallbackQuery):
    conn = sqlite3.connect('quiz.db')
    cursor = conn.cursor()
    cursor.execute("SELECT username, score FROM leaderboard ORDER BY score DESC LIMIT 5")
    top_players = cursor.fetchall()
    conn.close()

    if not top_players:
        await callback.message.answer("Таблица лидеров пока пуста. Стань первым!")
    else:
        text = "🏆 **ТОП-5 ИГРОКОВ:**\n\n"
        for i, player in enumerate(top_players, 1):
            text += f"{i}. {player[0]} — {player[1]} правильных\n"
        await callback.message.answer(text)
    await callback.answer()

@dp.callback_query(F.data == "start_quiz")
async def start_quiz_btn(callback: types.CallbackQuery, state: FSMContext):
    await cmd_quiz(callback.message, state)
    await callback.answer()

@dp.message(Command("quiz"))
async def cmd_quiz(message: types.Message, state: FSMContext):
    questions = get_random_questions()
    
    await state.update_data(questions=questions, current_index=0, score=0)
    await state.set_state(QuizStates.playing)
    
    await message.answer(f"🔥 Погнали! Вопрос 1 из {len(questions)}")
    await send_question(message, state)

async def send_question(message: types.Message, state: FSMContext):
    data = await state.get_data()
    questions = data['questions']
    index = data['current_index']

    if index >= len(questions):
        score = data['score']
        user_id = message.chat.id
        username = message.from_user.first_name
        
        conn = sqlite3.connect('quiz.db')
        cursor = conn.cursor()
        cursor.execute("SELECT score FROM leaderboard WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        if row is None or score > row[0]:
            cursor.execute("INSERT OR REPLACE INTO leaderboard (user_id, username, score) VALUES (?, ?, ?)", (user_id, username, score))
            conn.commit()
        conn.close()

        await state.clear()
        await message.answer(f"🏁 Квиз окончен! Твой счет: {score} из {len(questions)}.\nНажми /start для выхода в меню.")
        return

    q = questions[index]
    await message.answer(f"Вопрос {index + 1}:\n\n{q['text']}\n\nНапиши свой ответ в чат.")

@dp.message(QuizStates.playing)
async def check_answer(message: types.Message, state: FSMContext):
    if message.text.startswith('/'):
        return
        
    data = await state.get_data()
    questions = data['questions']
    index = data['current_index']
    
    correct_answer = questions[index]['answer'].lower().strip()
    user_answer = message.text.lower().strip()

    if user_answer == correct_answer:
        await state.update_data(score=data['score'] + 1)
        await message.answer("✅ Верно!")
    else:
        await message.answer(f"❌ Неверный ответ! Правильный ответ: {questions[index]['answer']}")
        
    await state.update_data(current_index=index + 1)
    await send_question(message, state)

async def main():
    print("Бот IQ_Quiz_bot запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())