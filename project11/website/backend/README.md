В цій папці буде знаходитись код для:

 - Отримання даних пульсу від ESP32 у реальному часі.
 - Збереження показників у базі SQLite для подальшого аналізу.  
 - Прийом записів емоцій від користувача та синхронізація з пульсом.
 - Аналітична обробка, що дозволяє створювати графіки та статистику.
 - Генерація автоматичних PDF та JSON звітів для користувача та спеціалістів.
 - Надання даних Frontend через API, щоб інтерфейс оновлювався миттєво.

## Встановлення

1. Створіть віртуальне середовище:
```bash
python -m venv venv
source venv/bin/activate  # На Windows: venv\Scripts\activate
```

2. Встановіть залежності:
```bash
pip install -r requirements.txt
```

3. Запустіть сервер:
```bash
python main.py
```

Або запустіть обидва сервери (frontend + backend) одночасно:
```bash
# З кореня проєкту
python start.py
# Або на Windows:
start.bat
# Або на Linux/Mac:
chmod +x start.sh
./start.sh
```

Сервер буде доступний за адресою: http://localhost:8000

API документація: http://localhost:8000/docs

## API Endpoints

- `POST /api/pulse` - Приймає дані пульсу від ESP32
- `GET /api/pulse/latest` - Останні дані пульсу
- `GET /api/pulse/history` - Історія пульсу за період
- `POST /api/emotions` - Створення запису емоції
- `GET /api/emotions` - Список записів емоцій
- `GET /api/stats/pulse` - Статистика пульсу
- `GET /api/stats/emotions` - Статистика емоцій
- `GET /api/analytics/correlation` - Аналіз кореляції
- `GET /api/report` - Генерація звіту
