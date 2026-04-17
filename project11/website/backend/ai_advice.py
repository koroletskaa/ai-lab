"""
Модуль для генерації порад за допомогою ШІ.
Приймає вже підготовлений контекст (статистика пульсу, емоцій, пікові моменти)
і повертає текст порад, згенерований мовною моделлю.
"""

from typing import Dict, Any
import json
import os

import requests


def generate_ai_advice(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Генерує психологічні поради щодо пульсу та емоцій.
    Всі рекомендації формує зовнішній ШІ (OpenAI). Якщо ключ відсутній
    або сталася помилка, повертається технічне повідомлення без ручних порад.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    user_context = json.dumps(context, ensure_ascii=False, indent=2)

    system_prompt = (
        "Ти — емпатичний психологічний асистент. "
        "Ти аналізуєш статистику пульсу та емоцій людини за останні дні. "
        "Твоє завдання — дати короткі, теплі й дуже практичні поради українською мовою.\n\n"
        "Важливо:\n"
        "- НЕ став діагнозів і не лякай користувача.\n"
        "- Наголошуй, що це не медична консультація.\n"
        "- Дай 4–7 конкретних порад: що можна спробувати ЗАРАЗ у звичайних життєвих ситуаціях "
        "(навчання, спілкування, відпочинок, онлайн-активності).\n"
        "- Орієнтуйся на середній пульс, найчастіші емоції та їхню інтенсивність.\n"
        "- Описуй приклади: що робити, коли відчуваєш тривогу/сум/злість у реальній ситуації.\n"
        "- Згадку про звернення до психолога чи психотерапевта використовуй максимум один раз наприкінці, мʼяко та без залякування.\n"
    )

    user_prompt = (
        "Ось дані про пульс та емоції користувача у форматі JSON.\n"
        "Проаналізуй їх і напиши структурований список порад.\n"
        "Обовʼязково:\n"
        "- покажи звʼязок між емоціями та можливими ситуаціями (наприклад, навчання, конфлікти, втома, соцмережі);\n"
        "- запропонуй конкретні прості дії (дихальні вправи, короткі ритуали підтримки, робота з думками, план відпочинку);\n"
        "- будь підтримувальним, без критики.\n\n"
        f"{user_context}\n"
    )

    if not api_key:
        # Немає ключа — не вигадуємо порад вручну
        return {
            "advice": "ШІ наразі не налаштований (немає OPENAI_API_KEY на сервері), тому поради недоступні.",
            "source": "missing_api_key",
            "has_ai": False,
            "model": None,
        }

    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.7,
            },
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        advice_text = (
            data.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
            .strip()
        )

        if not advice_text:
            return {
                "advice": "ШІ не зміг згенерувати поради. Спробуйте ще раз трохи пізніше.",
                "source": "ai_empty",
                "has_ai": False,
                "model": model,
            }

        return {
            "advice": advice_text,
            "source": "ai",
            "has_ai": True,
            "model": model,
        }
    except Exception as exc:
        # Будь-яка технічна помилка — повідомлення без порад
        return {
            "advice": "Сталася технічна помилка під час звернення до ШІ. Спробуйте пізніше.",
            "source": "ai_error",
            "has_ai": False,
            "model": model,
            "error": str(exc),
        }

