# 💓 Емоційний трекер - Пристрій та сайт-журнал емоцій з пульсометром

Проєкт випускної роботи: система для відстеження емоційного стану з інтеграцією пульсометра для занять із психотерапевтом.

## 📋 Опис проєкту

Емоційний трекер - це комплексна система, що поєднує:
- **Пристрій ESP32** з датчиком пульсу для моніторингу серцевого ритму
- **Backend API** (Python/FastAPI) для обробки та зберігання даних
- **Frontend веб-інтерфейс** для візуалізації та управління

Система дозволяє користувачу:
- Автоматично відстежувати пульс через пристрій ESP32
- Вносити записи про емоції з інтенсивністю та описом
- Бачити кореляцію між емоційним станом та фізіологічними показниками
- Генерувати звіти для психотерапевта

## 🏗️ Архітектура

```
┌─────────────┐      Wi-Fi      ┌──────────────┐      HTTP      ┌─────────────┐
│   ESP32     │ ───────────────> │   Backend    │ <───────────── │  Frontend   │
│ Pulse Sensor│                  │  (FastAPI)   │                │  (Web UI)   │
│   OLED      │                  │   SQLite     │                │   Charts    │
└─────────────┘                  └──────────────┘                └─────────────┘
```

## 📁 Структура проєкту

```
project11/
├── device/              # Код для ESP32 пристрою
│   ├── pulse_tracker.ino
│   ├── config.h.example
│   └── README.md
├── website/
│   ├── backend/         # Python FastAPI сервер
│   │   ├── main.py      # Основні API endpoints
│   │   ├── database.py  # Робота з SQLite
│   │   ├── models.py    # Моделі даних
│   │   ├── analytics.py # Аналітика та звіти
│   │   ├── requirements.txt
│   │   └── README.md
│   └── frontend/        # Веб-інтерфейс
│       ├── index.html
│       ├── styles.css
│       ├── app.js
│       └── README.md
├── AGENTS.md            # План проєкту
└── README.md            # Цей файл
```

## 🚀 Швидкий старт

### 1. Пристрій ESP32

1. Встановіть Arduino IDE та платформу ESP32
2. Встановіть бібліотеки: U8g2, ArduinoJson
3. Налаштуйте Wi-Fi у файлі `device/pulse_tracker.ino`
4. Завантажте код на плату

Детальні інструкції: [device/README.md](device/README.md)

### 2. Запуск серверів

**Швидкий старт (рекомендовано):**

Запустіть обидва сервери одночасно:

```bash
# Windows
start.bat

# Linux/Mac
chmod +x start.sh
./start.sh

# Або через Python (крос-платформенно)
python start.py
```

**Альтернатива - окремий запуск:**

Backend:
```bash
cd website/backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Frontend (в іншому терміналі):
```bash
cd website/frontend
python -m http.server 8080
```

- Backend API: `http://localhost:8000`
- API документація: `http://localhost:8000/docs`
- Frontend: `http://localhost:8080`

Детальні інструкції: [SETUP.md](SETUP.md)

## 🔧 Технології

- **Пристрій**: ESP32-C3, Pulse Sensor, OLED дисплей
- **Backend**: Python 3.8+, FastAPI, SQLite
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla), Plotly.js
- **Комунікація**: Wi-Fi (HTTP REST API)

## 📊 Функціонал

### Пристрій ESP32
- ✅ Зчитування пульсу через Pulse Sensor
- ✅ Фільтрація сигналу та виявлення піків
- ✅ Відображення BPM на OLED дисплеї
- ✅ Автоматична калібровка пульсу у спокої
- ✅ Передача даних на сервер через Wi-Fi

### Backend API
- ✅ Прийом даних пульсу від пристрою
- ✅ Зберігання в SQLite базі даних
- ✅ API для роботи з емоційними записами
- ✅ Синхронізація емоцій з пульсом за часом
- ✅ Аналітика та статистика
- ✅ Генерація звітів

### Frontend
- ✅ Моніторинг пульсу в реальному часі
- ✅ Форма додавання емоцій
- ✅ Інтерактивні графіки (Plotly.js)
- ✅ Журнал записів з фільтрацією
- ✅ Статистика та аналітика
- ✅ Генерація звітів

## 📡 API Endpoints

Основні endpoints:

- `POST /api/pulse` - Приймає дані пульсу від ESP32
- `GET /api/pulse/latest` - Останні дані пульсу
- `GET /api/pulse/history` - Історія пульсу
- `POST /api/emotions` - Створення запису емоції
- `GET /api/emotions` - Список записів емоцій
- `GET /api/stats/pulse` - Статистика пульсу
- `GET /api/stats/emotions` - Статистика емоцій
- `GET /api/analytics/correlation` - Кореляція емоції-пульс
- `GET /api/report` - Генерація звіту

Повна документація: `http://localhost:8000/docs`

## 🎯 Критерії успіху

- ✅ Система приймає та обробляє дані (пульс + емоції)
- ✅ Відстежуються 5+ основних емоцій
- ✅ Повністю функціональний інтерфейс
- ✅ Дані зберігаються без втрат
- ✅ Аналітика та звіти працюють

## 📝 Ліцензія

Проєкт створено для випускної роботи з основ інженерії штучного інтелекту.

## 👤 Автор

Королецька Софія Михайлівна, 11-Г

## 📚 Документація

- [План проєкту](AGENTS.md)
- [Документація пристрою](device/README.md)
- [Документація backend](website/backend/README.md)
- [Документація frontend](website/frontend/README.md)

