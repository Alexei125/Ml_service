# app/src/ml_model.py
import joblib
import os
from typing import Dict, Any

MODEL_PATH = "/app/ml_models/spam_classifier.pkl"
_vectorizer = None
_model = None


def load_model():
    """Загружает модель и векторизатор из файла."""
    global _vectorizer, _model
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(
            f"Модель не найдена по пути {MODEL_PATH}. Запустите train_model.py"
        )
    _vectorizer, _model = joblib.load(MODEL_PATH)
    print("✅ Модель загружена")


def predict(text: str) -> Dict[str, Any]:
    """Выполняет предсказание для текста."""
    if _vectorizer is None or _model is None:
        load_model()
    X = _vectorizer.transform([text])
    proba = _model.predict_proba(X)[0]
    pred_class = _model.predict(X)[0]
    confidence = max(proba)
    return {
        "class": "spam" if pred_class == 1 else "not_spam",
        "confidence": float(confidence),
    }
