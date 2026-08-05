# app/train_model.py
import joblib
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.linear_model import LogisticRegression
import os

# Небольшой обучающий набор (спам / не спам)
texts = [
    "Вы выиграли миллион долларов!",
    "Привет, как дела?",
    "Срочно! Ваш аккаунт заблокирован",
    "Хорошая погода сегодня",
    "Заработай 1000$ за час!",
    "Пойдём гулять?",
    "Скидка 90% только сегодня",
    "Какой твой любимый фильм?",
]
labels = [1, 0, 1, 0, 1, 0, 1, 0]  # 1 = спам, 0 = не спам

# Векторизация и обучение
vectorizer = CountVectorizer()
X = vectorizer.fit_transform(texts)
model = LogisticRegression()
model.fit(X, labels)

# Создаём папку, если её нет
os.makedirs("ml_models", exist_ok=True)

# Сохраняем модель и векторизатор
joblib.dump((vectorizer, model), "ml_models/spam_classifier.pkl")
print("✅ Модель обучена и сохранена в ml_models/spam_classifier.pkl")
