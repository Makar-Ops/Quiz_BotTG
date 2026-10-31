import sqlite3
import random

conn = sqlite3.connect('quiz.db')
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT,
    answer TEXT
)
''')

cursor.execute("DELETE from questions")

print("Генерация 10.000 вопросов...")

for i in range(1, 10001):
    text = f"Тестовый вопрос №{i}. Какое число является ответом?"
    answer = str(random.randint(1, 100))
    cursor.execute("INSERT INTO questions (text, answer) VALUES (?, ?)", (text, answer))

conn.commit()
conn.close()
print("✅ База данных quiz.db успешно создана! В ней 10 000 вопросов.")